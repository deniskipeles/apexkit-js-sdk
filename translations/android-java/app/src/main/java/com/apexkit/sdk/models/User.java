package com.apexkit.sdk.models;
import com.google.gson.annotations.SerializedName;
import java.util.Map;
public class User {
    public String id;
    public String email;
    public String role;
    public String scope;
    public Map<String, Object> metadata;
    @SerializedName("last_active") public String lastActive;
}
