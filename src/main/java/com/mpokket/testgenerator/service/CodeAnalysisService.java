package com.mpokket.testgenerator.service;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class CodeAnalysisService {

    public List<MethodInfo> analyzeJavaFile(String filePath) {
        List<MethodInfo> methodInfos = new ArrayList<>();
        
        try (FileInputStream in = new FileInputStream(filePath)) {
            JavaParser javaParser = new JavaParser();
            CompilationUnit cu = javaParser.parse(in).getResult().orElseThrow(() -> 
                new IOException("Failed to parse Java file"));
            
            cu.findAll(MethodDeclaration.class).forEach(method -> {
                MethodInfo methodInfo = new MethodInfo();
                methodInfo.setMethodName(method.getNameAsString());
                methodInfo.setReturnType(method.getType().asString());
                
                List<String> parameters = new ArrayList<>();
                for (Parameter param : method.getParameters()) {
                    parameters.add(param.getTypeAsString() + " " + param.getNameAsString());
                }
                methodInfo.setParameters(parameters);
                
                methodInfos.add(methodInfo);
            });
            
        } catch (IOException e) {
            log.error("Error analyzing file: " + filePath, e);
        }
        
        return methodInfos;
    }
    
    @Data
    public static class MethodInfo {
        private String methodName;
        private String returnType;
        private List<String> parameters;
    }
} 