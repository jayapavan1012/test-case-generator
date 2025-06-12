package com.example.service;

import java.util.List;
import java.util.ArrayList;

/**
 * A simple service class for demonstration purposes
 * Shows various patterns that would benefit from automated test generation
 */
public class SimpleTestService {
    
    private final List<String> data = new ArrayList<>();
    private boolean initialized = false;
    
    /**
     * Initializes the service
     */
    public void initialize() {
        if (!initialized) {
            data.clear();
            data.add("default");
            initialized = true;
        }
    }
    
    /**
     * Adds an item to the service
     * @param item the item to add
     * @throws IllegalArgumentException if item is null or empty
     */
    public void addItem(String item) {
        if (item == null || item.trim().isEmpty()) {
            throw new IllegalArgumentException("Item cannot be null or empty");
        }
        
        if (!initialized) {
            initialize();
        }
        
        data.add(item.trim());
    }
    
    /**
     * Removes an item from the service
     * @param item the item to remove
     * @return true if item was removed, false if not found
     */
    public boolean removeItem(String item) {
        if (item == null) {
            return false;
        }
        return data.remove(item.trim());
    }
    
    /**
     * Gets all items in the service
     * @return a copy of all items
     */
    public List<String> getAllItems() {
        return new ArrayList<>(data);
    }
    
    /**
     * Searches for items containing the given text
     * @param searchText the text to search for
     * @return list of matching items
     */
    public List<String> searchItems(String searchText) {
        if (searchText == null || searchText.trim().isEmpty()) {
            return new ArrayList<>();
        }
        
        return data.stream()
                .filter(item -> item.toLowerCase().contains(searchText.toLowerCase().trim()))
                .collect(ArrayList::new, ArrayList::add, ArrayList::addAll);
    }
    
    /**
     * Gets the count of items
     * @return number of items in the service
     */
    public int getItemCount() {
        return data.size();
    }
    
    /**
     * Checks if the service is empty
     * @return true if no items exist
     */
    public boolean isEmpty() {
        return data.isEmpty();
    }
    
    /**
     * Clears all items from the service
     */
    public void clear() {
        data.clear();
        initialized = false;
    }
    
    /**
     * Validates an item according to business rules
     * @param item the item to validate
     * @return true if valid, false otherwise
     */
    public boolean isValidItem(String item) {
        if (item == null) {
            return false;
        }
        
        String trimmed = item.trim();
        
        // Business rules
        return !trimmed.isEmpty() 
            && trimmed.length() >= 2 
            && trimmed.length() <= 100
            && !trimmed.contains("invalid");
    }
    
    /**
     * Processes a batch of items
     * @param items the items to process
     * @return number of successfully processed items
     */
    public int processBatch(List<String> items) {
        if (items == null) {
            return 0;
        }
        
        int processed = 0;
        for (String item : items) {
            try {
                if (isValidItem(item)) {
                    addItem(item);
                    processed++;
                }
            } catch (Exception e) {
                // Log error and continue
                System.err.println("Failed to process item: " + item);
            }
        }
        
        return processed;
    }
} 