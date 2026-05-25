package com.apexkit.sdk;

import com.apexkit.sdk.models.*;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import okhttp3.*;
import java.io.IOException;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class ApexKit {
    private String baseUrl;
    private String token;
    private User currentUser;
    private String scopeType = "root";
    private String scopeId = "";
    private OkHttpClient client;
    private Gson gson;

    public ApexKit(String baseUrl) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.client = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build();
        this.gson = new Gson();
    }

    public void setToken(String token, User user) {
        this.token = token;
        if (user != null) {
            this.currentUser = user;
            setScopeFromTag(user.scope);
        }
    }

    private void setScopeFromTag(String tag) {
        if ("root".equals(tag)) {
            scopeType = "root";
            scopeId = "";
        } else if (tag != null && tag.startsWith("tenant:")) {
            scopeType = "tenant";
            scopeId = tag.substring(7);
        } else if (tag != null && tag.startsWith("sandbox:")) {
            scopeType = "sandbox";
            scopeId = tag.substring(8);
        }
    }

    private Response executeRequest(String method, String endpoint, Object body, Map<String, String> params, boolean isRoot) throws IOException, ApexError {
        String path = endpoint;
        if (!isRoot && !endpoint.startsWith("/api/v1")) {
            path = endpoint.startsWith("/") ? "/api/v1" + endpoint : "/api/v1/" + endpoint;
        }

        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();
        if (params != null) {
            for (Map.Entry<String, String> entry : params.entrySet()) {
                urlBuilder.addQueryParameter(entry.getKey(), entry.getValue());
            }
        }

        Request.Builder requestBuilder = new Request.Builder().url(urlBuilder.build());
        if (token != null) {
            requestBuilder.header("Authorization", "Bearer " + token);
        }

        RequestBody requestBody = null;
        if (body != null) {
            requestBody = RequestBody.create(
                    MediaType.parse("application/json; charset=utf-8"),
                    gson.toJson(body)
            );
        } else if ("POST".equals(method) || "PUT".equals(method) || "PATCH".equals(method)) {
            requestBody = RequestBody.create(MediaType.parse("application/json; charset=utf-8"), "");
        }

        requestBuilder.method(method, requestBody);
        Response response = client.newCall(requestBuilder.build()).execute();

        if (!response.isSuccessful()) {
            String bodyStr = response.body().string();
            Map<String, Object> errorData;
            try {
                errorData = gson.fromJson(bodyStr, new TypeToken<Map<String, Object>>(){}.getType());
            } catch (Exception e) {
                errorData = new HashMap<>();
                errorData.put("message", bodyStr);
            }
            throw new ApexError(
                    (String) errorData.get("message"),
                    response.code(),
                    (String) errorData.get("error"),
                    errorData.get("details")
            );
        }

        return response;
    }

    public AuthNamespace auth() { return new AuthNamespace(); }
    public AdminsNamespace admins() { return new AdminsNamespace(); }
    public AiNamespace ai() { return new AiNamespace(); }
    public ScriptsNamespace scripts() { return new ScriptsNamespace(); }
    public FilesNamespace files() { return new FilesNamespace(); }

    public class AuthNamespace {
        public AuthResponse login(String email, String password) throws IOException, ApexError {
            Map<String, String> body = new HashMap<>();
            body.put("email", email);
            body.put("password", password);
            Response response = executeRequest("POST", "/auth/login", body, null, false);
            AuthResponse res = gson.fromJson(response.body().string(), AuthResponse.class);
            setToken(res.token, res.user);
            return res;
        }
        public AuthResponse register(String email, String password) throws IOException, ApexError {
            Map<String, String> body = new HashMap<>();
            body.put("email", email);
            body.put("password", password);
            Response response = executeRequest("POST", "/auth/register", body, null, false);
            AuthResponse res = gson.fromJson(response.body().string(), AuthResponse.class);
            setToken(res.token, res.user);
            return res;
        }
        public User getMe() throws IOException, ApexError {
            Response response = executeRequest("GET", "/auth/me", null, null, false);
            User user = gson.fromJson(response.body().string(), User.class);
            setScopeFromTag(user.scope);
            return user;
        }
        public void logout() {
            token = null;
            currentUser = null;
        }
    }

    public CollectionNamespace collection(String id) {
        return new CollectionNamespace(id);
    }

    public class CollectionNamespace {
        private String id;
        public CollectionNamespace(String id) { this.id = id; }

        public ListResult<BaseRecord> list(Map<String, String> options) throws IOException, ApexError {
            Response response = executeRequest("GET", "/collections/" + id + "/records", null, options, false);
            Type type = new TypeToken<ListResult<BaseRecord>>(){}.getType();
            return gson.fromJson(response.body().string(), type);
        }
        public BaseRecord create(Map<String, Object> data) throws IOException, ApexError {
            Map<String, Object> body = new HashMap<>();
            body.put("data", data);
            Response response = executeRequest("POST", "/collections/" + id + "/records", body, null, false);
            return gson.fromJson(response.body().string(), BaseRecord.class);
        }
        public BaseRecord get(String recordId, Map<String, String> options) throws IOException, ApexError {
            Response response = executeRequest("GET", "/collections/" + id + "/records/" + recordId, null, options, false);
            return gson.fromJson(response.body().string(), BaseRecord.class);
        }
        public BaseRecord update(String recordId, Map<String, Object> data) throws IOException, ApexError {
            Map<String, Object> body = new HashMap<>();
            body.put("data", data);
            Response response = executeRequest("PUT", "/collections/" + id + "/records/" + recordId, body, null, false);
            return gson.fromJson(response.body().string(), BaseRecord.class);
        }
        public void delete(String recordId) throws IOException, ApexError {
            executeRequest("DELETE", "/collections/" + id + "/records/" + recordId, null, null, false);
        }
    }

    public class AdminsNamespace {
        public List<Map<String, Object>> listCollections() throws IOException, ApexError {
            Response response = executeRequest("GET", "/collections", null, null, false);
            return gson.fromJson(response.body().string(), new TypeToken<List<Map<String, Object>>>(){}.getType());
        }
    }

    public class AiNamespace {
        public Map<String, Object> run(String slug, Map<String, Object> variables) throws IOException, ApexError {
            Map<String, Object> body = new HashMap<>();
            body.put("variables", variables);
            Response response = executeRequest("POST", "/ai/run/" + slug, body, null, false);
            return gson.fromJson(response.body().string(), new TypeToken<Map<String, Object>>(){}.getType());
        }
    }

    public class ScriptsNamespace {
        public Object run(String name, Object variables) throws IOException, ApexError {
            Response response = executeRequest("POST", "/run/" + name, variables, null, false);
            return gson.fromJson(response.body().string(), Object.class);
        }
    }

    public class FilesNamespace {
        public String getFileUrl(String filename) {
            if (filename.startsWith("http")) return filename;
            return baseUrl + "/api/v1/storage/file/" + (filename.startsWith("/") ? filename.substring(1) : filename);
        }
    }

    public Map<String, Object> graphql(String query, Map<String, Object> variables) throws IOException, ApexError {
        Map<String, Object> body = new HashMap<>();
        body.put("query", query);
        body.put("variables", variables != null ? variables : new HashMap<>());
        Response response = executeRequest("POST", "/graphql", body, null, true);
        return gson.fromJson(response.body().string(), new TypeToken<Map<String, Object>>(){}.getType());
    }
}
