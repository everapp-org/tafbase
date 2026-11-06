---
id: CONCEPT-java-v1-022-01-java-http-client
status: accepted
subproject: java
layer: L2-language
since: Java 11
standing: recommended
---

# Modern Java HTTP Client

## Definition

The built-in `java.net.http.HttpClient` provides modern HTTP/1.1 and HTTP/2 client capabilities supporting synchronous blocking calls, asynchronous non-blocking calls (`CompletableFuture`), reactive streams, and pluggable body handlers.

```java
HttpClient client = HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_2)
    .connectTimeout(Duration.ofSeconds(5))
    .build();

HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/v1/metrics"))
    .header("Accept", "application/json")
    .timeout(Duration.ofSeconds(10))
    .GET()
    .build();

HttpResponse<String> response = client.send(
    request,
    HttpResponse.BodyHandlers.ofString()
);

if (response.statusCode() == 200) {
    System.out.println("Payload: " + response.body());
}
```

## Why it exists

Replaces the archaic, cumbersome `HttpURLConnection` API from Java 1.1, which lacked HTTP/2 support, had awkward streaming mechanics, conflated connections with requests, and lacked modern timeout configurations. It also removes the mandatory dependency on external HTTP libraries for standard enterprise microservices and utilities.
