package com.apexkit.sdk

import com.apexkit.sdk.models.*
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApexKit(baseUrl: String) {
    private val baseUrl = baseUrl.removeSuffix("/")
    private var token: String? = null
    private var currentUser: User? = null
    private var scopeType: String = "root"
    private var scopeId: String = ""
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()
    private val gson = Gson()

    fun sandbox(uuid: String): ApexKit {
        val instance = ApexKit("${this.baseUrl}/sandbox/$uuid")
        instance.scopeType = "sandbox"
        instance.scopeId = uuid
        instance.setToken(this.token ?: "", this.currentUser)
        return instance
    }

    fun tenant(tenantId: String): ApexKit {
        val instance = ApexKit("${this.baseUrl}/tenant/$tenantId")
        instance.scopeType = "tenant"
        instance.scopeId = tenantId
        instance.setToken(this.token ?: "", this.currentUser)
        return instance
    }

    fun setToken(token: String, user: User?) {
        this.token = token
        if (user != null) {
            this.currentUser = user
            setScopeFromTag(user.scope)
        }
    }

    private fun setScopeFromTag(tag: String) {
        when {
            tag == "root" -> {
                scopeType = "root"
                scopeId = ""
            }
            tag.startsWith("tenant:") -> {
                scopeType = "tenant"
                scopeId = tag.removePrefix("tenant:")
            }
            tag.startsWith("sandbox:") -> {
                scopeType = "sandbox"
                scopeId = tag.removePrefix("sandbox:")
            }
        }
    }

    private fun request(
        method: String,
        endpoint: String,
        body: Any? = null,
        params: Map<String, String>? = null,
        isRoot: Boolean = false
    ): Response {
        var path = endpoint
        if (!isRoot && !endpoint.startsWith("/api/v1")) {
            path = if (endpoint.startsWith("/")) "/api/v1$endpoint" else "/api/v1/$endpoint"
        }

        val urlBuilder = HttpUrl.parse("$baseUrl$path")!!.newBuilder()
        params?.forEach { (k, v) -> urlBuilder.addQueryParameter(k, v) }

        val requestBuilder = Request.Builder().url(urlBuilder.build())
        token?.let { requestBuilder.header("Authorization", "Bearer $it") }

        val requestBody = if (body != null) {
            val mediaType = "application/json; charset=utf-8".toMediaType()
            gson.toJson(body).toRequestBody(mediaType)
        } else if (method == "POST" || method == "PUT" || method == "PATCH") {
            "".toRequestBody(null)
        } else {
            null
        }

        requestBuilder.method(method, requestBody)
        val response = client.newCall(requestBuilder.build()).execute()

        if (!response.isSuccessful) {
            val bodyStr = response.body?.string() ?: ""
            val errorData = try {
                gson.fromJson(bodyStr, Map::class.java)
            } catch (e: Exception) {
                mapOf("message" to bodyStr)
            }
            throw ApexError(
                errorData["message"] as? String ?: "API Error",
                response.code,
                errorData["error"] as? String,
                errorData["details"]
            )
        }

        return response
    }

    val auth = AuthNamespace()
    val admins = AdminsNamespace()
    val ai = AiNamespace()
    val scripts = ScriptsNamespace()
    val files = FilesNamespace()

    inner class AuthNamespace {
        fun login(email: String, password: String): AuthResponse {
            val response = request("POST", "/auth/login", mapOf("email" to email, "password" to password))
            val authRes = gson.fromJson(response.body?.string(), AuthResponse::class.java)
            setToken(authRes.token, authRes.user)
            return authRes
        }

        fun register(email: String, password: String): AuthResponse {
            val response = request("POST", "/auth/register", mapOf("email" to email, "password" to password))
            val authRes = gson.fromJson(response.body?.string(), AuthResponse::class.java)
            setToken(authRes.token, authRes.user)
            return authRes
        }

        fun getMe(): User {
            val response = request("GET", "/auth/me")
            val user = gson.fromJson(response.body?.string(), User::class.java)
            setScopeFromTag(user.scope)
            return user
        }

        fun logout() {
            token = null
            currentUser = null
        }
    }

    fun collection(id: String) = CollectionNamespace(id)

    inner class CollectionNamespace(val id: String) {
        fun list(options: Map<String, String>? = null): ListResult<BaseRecord> {
            val response = request("GET", "/collections/$id/records", params = options)
            val type = object : TypeToken<ListResult<BaseRecord>>() {}.type
            return gson.fromJson(response.body?.string(), type)
        }

        fun create(data: Map<String, Any>): BaseRecord {
            val response = request("POST", "/collections/$id/records", body = mapOf("data" to data))
            return gson.fromJson(response.body?.string(), BaseRecord::class.java)
        }

        fun get(recordId: String, options: Map<String, String>? = null): BaseRecord {
            val response = request("GET", "/collections/$id/records/$recordId", params = options)
            return gson.fromJson(response.body?.string(), BaseRecord::class.java)
        }

        fun update(recordId: String, data: Map<String, Any>): BaseRecord {
            val response = request("PUT", "/collections/$id/records/$recordId", body = mapOf("data" to data))
            return gson.fromJson(response.body?.string(), BaseRecord::class.java)
        }

        fun patch(recordId: String, data: Map<String, Any>): BaseRecord {
            val response = request("PATCH", "/collections/$id/records/$recordId", body = mapOf("data" to data))
            return gson.fromJson(response.body?.string(), BaseRecord::class.java)
        }

        fun delete(recordId: String) {
            request("DELETE", "/collections/$id/records/$recordId")
        }
    }

    inner class AdminsNamespace {
        fun listCollections(): List<Map<String, Any>> {
            val response = request("GET", "/collections")
            val type = object : TypeToken<List<Map<String, Any>>>() {}.type
            return gson.fromJson(response.body?.string(), type)
        }
    }

    inner class AiNamespace {
        fun run(slug: String, variables: Map<String, Any>): Map<String, Any> {
            val response = request("POST", "/ai/run/$slug", mapOf("variables" to variables))
            val type = object : TypeToken<Map<String, Any>>() {}.type
            return gson.fromJson(response.body?.string(), type)
        }
    }

    inner class ScriptsNamespace {
        fun run(name: String, variables: Any): Any {
            val response = request("POST", "/run/$name", variables)
            val type = object : TypeToken<Any>() {}.type
            return gson.fromJson(response.body?.string(), type)
        }
    }

    inner class FilesNamespace {
        fun getFileUrl(filename: String): String {
            if (filename.startsWith("http")) return filename
            return "$baseUrl/api/v1/storage/file/${filename.removePrefix("/")}"
        }
    }

    fun graphql(query: String, variables: Map<String, Any>? = null): Map<String, Any> {
        val response = request("POST", "/graphql", mapOf("query" to query, "variables" to (variables ?: emptyMap<String, Any>())), isRoot = true)
        val type = object : TypeToken<Map<String, Any>>() {}.type
        return gson.fromJson(response.body?.string(), type)
    }
}
