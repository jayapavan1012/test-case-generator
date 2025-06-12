import com.mpokket.testgenerator.controller.DeepSeekTestController;
import com.mpokket.testgenerator.service.DeepSeekCoderService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.util.Map;
import java.util.HashMap;

@ExtendWith(MockitoExtension.class)
public class DeepSeekTestControllerTest {

    @Mock
    private DeepSeekCoderService deepSeekCoderService;

    @InjectMocks
    private DeepSeekTestController deepseektestcontroller;

    @BeforeEach
    public void setUp() {
        // Setup is handled by Mockito annotations
    }

    @Test
        public void testHealthSuccess() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.isModelReady()).thenReturn(true);
            when(deepSeekCoderService.getSystemStatus()).thenReturn(new HashMap<>());
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            ResponseEntity<Map<String, Object>> response = controller.health();
    
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertNotNull(response.getBody());
            assertTrue((boolean) response.getBody().get("model_ready"));
        }
    @Test
        public void testHealthFailure() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.isModelReady()).thenReturn(false);
            when(deepSeekCoderService.getSystemStatus()).thenReturn(new HashMap<>());
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            ResponseEntity<Map<String, Object>> response = controller.health();
    
            assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
            assertNotNull(response.getBody());
            assertFalse((boolean) response.getBody().get("model_ready"));
        }
    @Test
        public void testInitializeModelSuccess() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.initializeModel()).thenReturn(true);
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            ResponseEntity<Map<String, Object>> response = controller.initializeModel();
    
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertNotNull(response.getBody());
            assertTrue((boolean) response.getBody().get("status"));
        }
    @Test
        public void testInitializeModelFailure() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.initializeModel()).thenReturn(false);
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            ResponseEntity<Map<String, Object>> response = controller.initializeModel();
    
            assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
            assertNotNull(response.getBody());
            assertFalse((boolean) response.getBody().get("status"));
        }
    @Test
        public void testGetSystemStatusSuccess() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            Map<String, Object> expectedStatus = new HashMap<>();
            expectedStatus.put("status", "success");
            expectedStatus.put("message", "Deepseek-Coder cache cleared successfully");
            when(deepSeekCoderService.getSystemStatus()).thenReturn(expectedStatus);
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.setDeepSeekCoderService(deepSeekCoderService);
    
            ResponseEntity<Map<String, Object>> response = controller.getSystemStatus();
    
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertEquals(expectedStatus, response.getBody());
            verify(deepSeekCoderService).getSystemStatus();
        }
    @Test
        public void testGetSystemStatusFailure() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.getSystemStatus()).thenThrow(new RuntimeException("Service error"));
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.setDeepSeekCoderService(deepSeekCoderService);
    
            ResponseEntity<Map<String, Object>> response = controller.getSystemStatus();
    
            assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
            Map<String, Object> errorResponse = response.getBody();
            assertEquals("Failed to get system status: Service error", errorResponse.get("error"));
            verify(deepSeekCoderService).getSystemStatus();
        }
    @Test
        public void testClearCacheSuccess() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.clearCache()).thenReturn(true);
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.setDeepSeekCoderService(deepSeekCoderService);
    
            ResponseEntity<Map<String, Object>> response = controller.clearCache();
    
            assertEquals(HttpStatus.OK, response.getStatusCode());
            Map<String, Object> responseBody = response.getBody();
            assertEquals("success", responseBody.get("status"));
            assertEquals("Deepseek-Coder cache cleared successfully", responseBody.get("message"));
            verify(deepSeekCoderService).clearCache();
        }
    @Test
        public void testClearCacheFailure() {
            DeepSeekCoderService deepSeekCoderService = mock(DeepSeekCoderService.class);
            when(deepSeekCoderService.clearCache()).thenReturn(false);
    
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.setDeepSeekCoderService(deepSeekCoderService);
    
            ResponseEntity<Map<String, Object>> response = controller.clearCache();
    
            assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
            Map<String, Object> errorResponse = response.getBody();
            assertEquals("Failed to clear cache", errorResponse.get("message"));
            verify(deepSeekCoderService).clearCache();
        }
    @Test
        public void testDeepSeekV2Success() {
            DeepSeekCoderService deepSeekCoderService = Mockito.mock(DeepSeekCoderService.class);
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            Map<String, Object> result = new HashMap<>();
            result.put("status", "success");
            when(deepSeekCoderService.testDeepSeekV2Connection()).thenReturn(result);
    
            ResponseEntity<Map<String, Object>> response = controller.testDeepSeekV2();
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertEquals("success", response.getBody().get("status"));
        }
    @Test
        public void testDeepSeekV2Failure() {
            DeepSeekCoderService deepSeekCoderService = Mockito.mock(DeepSeekCoderService.class);
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            Map<String, Object> result = new HashMap<>();
            result.put("status", "error");
            when(deepSeekCoderService.testDeepSeekV2Connection()).thenReturn(result);
    
            ResponseEntity<Map<String, Object>> response = controller.testDeepSeekV2();
            assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
            assertEquals("error", response.getBody().get("status"));
        }
    @Test
        public void testGetModelsStatusSuccess() {
            DeepSeekCoderService deepSeekCoderService = Mockito.mock(DeepSeekCoderService.class);
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            Map<String, Object> status = new HashMap<>();
            status.put("status", "success");
            when(deepSeekCoderService.getModelsStatus()).thenReturn(status);
    
            ResponseEntity<Map<String, Object>> response = controller.getModelsStatus();
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertEquals("success", response.getBody().get("status"));
        }
    @Test
        public void testGetModelsStatusFailure() {
            DeepSeekCoderService deepSeekCoderService = Mockito.mock(DeepSeekCoderService.class);
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            Map<String, Object> status = new HashMap<>();
            status.put("status", "error");
            when(deepSeekCoderService.getModelsStatus()).thenReturn(status);
    
            ResponseEntity<Map<String, Object>> response = controller.getModelsStatus();
            assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
            assertEquals("error", response.getBody().get("error"));
        }
    @Test
        public void testGenerateAndSaveTestSuccess() {
            DeepSeekCoderService deepSeekCoderService = Mockito.mock(DeepSeekCoderService.class);
            DeepSeekTestController controller = new DeepSeekTestController();
            controller.deepSeekCoderService = deepSeekCoderService;
    
            Map<String, String> request = new HashMap<>();
            request.put("filePath", "testFilePath");
            when(deepSeekCoderService.generateTestAndSave("testFilePath")).thenReturn(Map.of("testFilePath", "testFilePath", "modelUsed", "model"));
    
            ResponseEntity<Map<String, Object>> response = controller.generateAndSaveTest(request);
            assertEquals(HttpStatus.OK, response.getStatusCode());
            assertEquals("success", response.getBody().get("status"));
        }
}