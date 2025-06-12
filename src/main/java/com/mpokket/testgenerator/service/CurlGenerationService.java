package com.mpokket.testgenerator.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class CurlGenerationService {

    private static final Logger logger = LoggerFactory.getLogger(CurlGenerationService.class);

    private final RestTemplate restTemplate;

    @Value("${curl.generator.api.url}")
    private String curlGeneratorApiUrl;

    public CurlGenerationService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Orchestrates the generation of a curl script.
     * @param controllerPath The absolute path to the Java controller file.
     * @param scenarios      The user-provided scenarios as a string.
     * @return The content of the generated shell script.
     * @throws IOException If file reading fails.
     */
    public String generateCurlScript(Path controllerPath, String scenarios) throws IOException {
        logger.info("Starting curl script generation for: {}", controllerPath);

        // 1. Read the controller file content
        String controllerCode = new String(Files.readAllBytes(controllerPath));
        
        // 2. Discover and read DTOs
        Map<String, String> dtoCodes = findAndReadDtos(controllerCode, controllerPath);

        // 3. Prepare the request for the Python AI service
        Map<String, Object> requestPayload = new HashMap<>();
        requestPayload.put("controller_code", controllerCode);
        requestPayload.put("dto_codes", dtoCodes);
        requestPayload.put("scenarios", scenarios);
        // Assuming the Spring Boot app runs on 8080 by default
        requestPayload.put("base_url", "http://localhost:8080");

        logger.info("Sending request to AI curl generator at: {}", curlGeneratorApiUrl);
        
        // 4. Call the Python service
        Map<String, String> response = restTemplate.postForObject(curlGeneratorApiUrl, requestPayload, Map.class);

        if (response == null || !response.containsKey("script_content")) {
            logger.error("Failed to get a valid script from AI service. Response was null or malformed.");
            throw new RuntimeException("Failed to generate curl script: AI service returned an invalid response.");
        }

        logger.info("Successfully received generated script from AI service.");
        return response.get("script_content");
    }

    /**
     * Finds DTOs mentioned in @RequestBody, locates them, and reads their content.
     * @param controllerCode The source code of the controller.
     * @param controllerPath The path to the controller file.
     * @return A map of DTO file names to their source code.
     */
    private Map<String, String> findAndReadDtos(String controllerCode, Path controllerPath) {
        Map<String, String> dtoCodes = new HashMap<>();
        
        // Regex to find class names inside @RequestBody annotations
        Pattern requestBodyPattern = Pattern.compile("@RequestBody\\s+([\\w\\.<>]+)\\s+\\w+");
        Matcher requestBodyMatcher = requestBodyPattern.matcher(controllerCode);

        while (requestBodyMatcher.find()) {
            String dtoClassName = requestBodyMatcher.group(1);
            // Handle generic types like List<UserDto>
            if (dtoClassName.contains("<")) {
                dtoClassName = dtoClassName.substring(dtoClassName.indexOf("<") + 1, dtoClassName.indexOf(">"));
            }
            logger.info("Found potential DTO in @RequestBody: {}", dtoClassName);

            try {
                // Find the full path of the DTO from import statements
                Path dtoPath = findDtoPathFromImports(controllerCode, controllerPath, dtoClassName);
                if (dtoPath != null && Files.exists(dtoPath)) {
                    String dtoCode = new String(Files.readAllBytes(dtoPath));
                    dtoCodes.put(dtoPath.getFileName().toString(), dtoCode);
                    logger.info("Successfully read DTO file: {}", dtoPath);
                } else {
                     logger.warn("Could not find or read DTO file for class: {}", dtoClassName);
                }
            } catch (IOException e) {
                logger.error("Error reading DTO file for class " + dtoClassName, e);
            }
        }
        return dtoCodes;
    }

    /**
     * Tries to locate a DTO file path based on import statements in the controller.
     * @param controllerCode  The source code of the controller.
     * @param controllerPath  The path of the controller file.
     * @param dtoClassName    The simple name of the DTO class to find.
     * @return The resolved Path to the DTO file, or null if not found.
     */
    private Path findDtoPathFromImports(String controllerCode, Path controllerPath, String dtoClassName) {
        // Regex to find the import statement for the given class name
        Pattern importPattern = Pattern.compile("import\\s+([\\w\\.]+\\." + dtoClassName + ");");
        Matcher importMatcher = importPattern.matcher(controllerCode);

        if (importMatcher.find()) {
            String fullClassName = importMatcher.group(1);
            logger.info("Found import for DTO: {}", fullClassName);
            
            // This is a bit of a guess. It assumes a standard Maven/Gradle layout.
            // It replaces the package name dots with path separators.
            String relativePath = fullClassName.replace('.', '/') + ".java";
            
            // We need to find the "root" of the source, e.g., 'src/main/java'
            // We walk up from the controller's path until we find a common root.
            Path current = controllerPath.getParent();
            while(current != null) {
                Path potentialPath = current.resolve(relativePath);
                if (Files.exists(potentialPath)) {
                    return potentialPath;
                }
                // A simplistic check to find the source root
                if(current.endsWith("src/main/java") || current.endsWith("src\\main\\java")) {
                     // If we are at the root, try constructing path from here.
                     Path resolvedPath = Paths.get(current.toString(), relativePath);
                     if(Files.exists(resolvedPath)) {
                         return resolvedPath;
                     }
                     break; 
                }
                current = current.getParent();
            }
            // Fallback for when the project structure is non-standard
            logger.warn("Could not resolve DTO path for '{}'. You may need to adjust the path resolution logic.", fullClassName);
        }
        return null;
    }
} 