package com.apexkit.sdk;

public class ApexError extends Exception {
    public int status;
    public String code;
    public Object details;

    public ApexError(String message, int status, String code, Object details) {
        super(message);
        this.status = status;
        this.code = code;
        this.details = details;
    }
}
