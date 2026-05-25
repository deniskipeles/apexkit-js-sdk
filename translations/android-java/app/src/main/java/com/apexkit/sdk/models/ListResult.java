package com.apexkit.sdk.models;
import com.google.gson.annotations.SerializedName;
import java.util.List;
public class ListResult<T> {
    public List<T> items;
    public int total;
    public Integer page;
    @SerializedName("per_page") public Integer perPage;
}
