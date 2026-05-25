package com.apexkit.sdk.models

import com.google.gson.annotations.SerializedName

data class User(
    val id: String,
    val email: String,
    val role: String,
    val scope: String,
    val metadata: Map<String, Any>? = null,
    @SerializedName("last_active") val lastActive: String? = null
)

data class AuthResponse(
    val token: String,
    val user: User
)

data class BaseRecord(
    val id: String,
    val created: String,
    val updated: String,
    val data: Map<String, Any>,
    val expand: Map<String, Any>
)

data class ListResult<T>(
    val items: List<T>,
    val total: Int,
    val page: Int? = null,
    @SerializedName("per_page") val perPage: Int? = null
)

class ApexError(
    message: String,
    val status: Int = 500,
    val code: String? = null,
    val details: Any? = null
) : Exception(message)
