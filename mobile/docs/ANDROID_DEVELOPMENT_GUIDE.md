# ZiggyAI Android App Development Guide

## Overview

This guide explains how to build an Android application for ZiggyAI using the Mobile API. The recommended approach uses modern Android development practices with Kotlin, Jetpack Compose, and Clean Architecture.

## Technology Stack

### Recommended Stack

- **Language**: Kotlin 1.9+
- **UI Framework**: Jetpack Compose
- **Architecture**: MVVM + Clean Architecture
- **Dependency Injection**: Hilt
- **Networking**: Retrofit + OkHttp
- **Database**: Room
- **Async**: Coroutines + Flow
- **Push Notifications**: Firebase Cloud Messaging (FCM)

## Project Setup

### 1. Create New Android Project

```bash
# Using Android Studio or command line
# Minimum SDK: 24 (Android 7.0)
# Target SDK: 34 (Android 14)
```

### 2. Add Dependencies

**build.gradle.kts (Project level):**

```kotlin
plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
    id("com.google.dagger.hilt.android") version "2.48" apply false
    id("com.google.gms.google-services") version "4.4.0" apply false
}
```

**build.gradle.kts (App level):**

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("kotlin-kapt")
    id("dagger.hilt.android.plugin")
    id("com.google.gms.google-services")
}

android {
    namespace = "com.ziggyai.mobile"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.ziggyai.mobile"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        buildConfigField("String", "API_BASE_URL", "\"https://api.ziggyai.com/mobile\"")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }
}

dependencies {
    // Compose
    implementation(platform("androidx.compose:compose-bom:2024.01.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.navigation:navigation-compose:2.7.6")

    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Dependency Injection
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

    // Room Database
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3")

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-messaging-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")

    // WorkManager for background sync
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    // DataStore for preferences
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    // Charts
    implementation("com.github.PhilJay:MPAndroidChart:v3.1.0")

    // Security
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
}
```

## Project Structure

```
app/
├── src/
│   ├── main/
│   │   ├── java/com/ziggyai/mobile/
│   │   │   ├── ZiggyApplication.kt
│   │   │   ├── data/
│   │   │   │   ├── api/
│   │   │   │   │   ├── ZiggyApiService.kt
│   │   │   │   │   ├── AuthInterceptor.kt
│   │   │   │   │   └── models/
│   │   │   │   ├── local/
│   │   │   │   │   ├── ZiggyDatabase.kt
│   │   │   │   │   ├── dao/
│   │   │   │   │   └── entities/
│   │   │   │   ├── repository/
│   │   │   │   │   ├── AuthRepository.kt
│   │   │   │   │   ├── MarketRepository.kt
│   │   │   │   │   ├── SignalRepository.kt
│   │   │   │   │   └── PortfolioRepository.kt
│   │   │   │   └── preferences/
│   │   │   │       └── UserPreferences.kt
│   │   │   ├── domain/
│   │   │   │   ├── model/
│   │   │   │   └── usecase/
│   │   │   ├── ui/
│   │   │   │   ├── theme/
│   │   │   │   ├── navigation/
│   │   │   │   ├── screens/
│   │   │   │   │   ├── login/
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   ├── market/
│   │   │   │   │   ├── signals/
│   │   │   │   │   ├── portfolio/
│   │   │   │   │   ├── alerts/
│   │   │   │   │   └── settings/
│   │   │   │   └── components/
│   │   │   ├── util/
│   │   │   ├── workers/
│   │   │   │   └── SyncWorker.kt
│   │   │   └── di/
│   │   │       ├── AppModule.kt
│   │   │       ├── NetworkModule.kt
│   │   │       └── DatabaseModule.kt
│   │   ├── res/
│   │   └── AndroidManifest.xml
│   └── test/
└── build.gradle.kts
```

## Implementation Guide

### 1. Application Class

**ZiggyApplication.kt:**

```kotlin
package com.ziggyai.mobile

import android.app.Application
import androidx.work.*
import com.ziggyai.mobile.workers.SyncWorker
import dagger.hilt.android.HiltAndroidApp
import java.util.concurrent.TimeUnit

@HiltAndroidApp
class ZiggyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        setupWorkManager()
    }

    private fun setupWorkManager() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
            15, TimeUnit.MINUTES
        )
            .setConstraints(constraints)
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                10, TimeUnit.SECONDS
            )
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "ziggy_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )
    }
}
```

### 2. API Service

**ZiggyApiService.kt:**

```kotlin
package com.ziggyai.mobile.data.api

import com.ziggyai.mobile.data.api.models.*
import retrofit2.Response
import retrofit2.http.*

interface ZiggyApiService {
    // Authentication
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @POST("auth/refresh")
    suspend fun refreshToken(@Body refreshToken: String): Response<TokenResponse>

    @POST("auth/logout")
    suspend fun logout(): Response<Unit>

    // Device Management
    @POST("device/register")
    suspend fun registerDevice(@Body deviceInfo: DeviceInfo): Response<DeviceRegistrationResponse>

    // Market Data
    @GET("market/snapshot")
    suspend fun getMarketSnapshot(
        @Query("symbols") symbols: String
    ): Response<MarketSnapshotResponse>

    @GET("market/quote/{symbol}")
    suspend fun getQuote(@Path("symbol") symbol: String): Response<QuoteResponse>

    // Signals
    @GET("signals")
    suspend fun getSignals(
        @Query("limit") limit: Int = 10,
        @Query("symbols") symbols: String? = null
    ): Response<List<SignalResponse>>

    // Portfolio
    @GET("portfolio")
    suspend fun getPortfolio(): Response<PortfolioResponse>

    // Alerts
    @GET("alerts")
    suspend fun getAlerts(
        @Query("active_only") activeOnly: Boolean = true
    ): Response<List<AlertResponse>>

    @POST("alerts")
    suspend fun createAlert(@Body alert: CreateAlertRequest): Response<AlertResponse>

    @DELETE("alerts/{alertId}")
    suspend fun deleteAlert(@Path("alertId") alertId: String): Response<Unit>

    // News
    @GET("news")
    suspend fun getNews(
        @Query("limit") limit: Int = 20,
        @Query("symbols") symbols: String? = null
    ): Response<List<NewsResponse>>

    // Efficient Sync
    @GET("sync")
    suspend fun sync(
        @Query("since") since: Long? = null,
        @Query("include") include: String = "all"
    ): Response<SyncResponse>

    // Health
    @GET("health")
    suspend fun healthCheck(): Response<HealthResponse>
}
```

### 3. Network Module (Dependency Injection)

**NetworkModule.kt:**

```kotlin
package com.ziggyai.mobile.di

import com.ziggyai.mobile.BuildConfig
import com.ziggyai.mobile.data.api.AuthInterceptor
import com.ziggyai.mobile.data.api.ZiggyApiService
import com.ziggyai.mobile.data.preferences.UserPreferences
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideAuthInterceptor(
        userPreferences: UserPreferences
    ): AuthInterceptor {
        return AuthInterceptor(userPreferences)
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor
    ): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .addInterceptor(authInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideZiggyApiService(retrofit: Retrofit): ZiggyApiService {
        return retrofit.create(ZiggyApiService::class.java)
    }
}
```

### 4. Auth Interceptor

**AuthInterceptor.kt:**

```kotlin
package com.ziggyai.mobile.data.api

import com.ziggyai.mobile.data.preferences.UserPreferences
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(
    private val userPreferences: UserPreferences
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = runBlocking {
            userPreferences.getAccessToken().first()
        }

        val request = if (token != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }

        return chain.proceed(request)
    }
}
```

### 5. Repository Pattern

**MarketRepository.kt:**

```kotlin
package com.ziggyai.mobile.data.repository

import com.ziggyai.mobile.data.api.ZiggyApiService
import com.ziggyai.mobile.data.local.dao.QuoteDao
import com.ziggyai.mobile.data.local.entities.QuoteEntity
import com.ziggyai.mobile.domain.model.Quote
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MarketRepository @Inject constructor(
    private val api: ZiggyApiService,
    private val quoteDao: QuoteDao
) {
    fun getQuotes(symbols: List<String>): Flow<Result<List<Quote>>> = flow {
        // Emit cached data first
        val cached = quoteDao.getQuotes(symbols).map { it.toDomain() }
        emit(Result.success(cached))

        // Fetch fresh data
        try {
            val response = api.getMarketSnapshot(symbols.joinToString(","))
            if (response.isSuccessful) {
                response.body()?.let { snapshot ->
                    // Update cache
                    val entities = snapshot.quotes.map { it.toEntity() }
                    quoteDao.insertAll(entities)

                    // Emit fresh data
                    emit(Result.success(snapshot.quotes.map { it.toDomain() }))
                }
            } else {
                emit(Result.failure(Exception("API error: ${response.code()}")))
            }
        } catch (e: Exception) {
            // Return cached data on error
            emit(Result.failure(e))
        }
    }

    suspend fun refreshQuote(symbol: String): Result<Quote> {
        return try {
            val response = api.getQuote(symbol)
            if (response.isSuccessful) {
                response.body()?.let { quote ->
                    quoteDao.insert(quote.toEntity())
                    Result.success(quote.toDomain())
                } ?: Result.failure(Exception("Empty response"))
            } else {
                Result.failure(Exception("API error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### 6. Background Sync Worker

**SyncWorker.kt:**

```kotlin
package com.ziggyai.mobile.workers

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.ziggyai.mobile.data.preferences.UserPreferences
import com.ziggyai.mobile.data.repository.SyncRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val syncRepository: SyncRepository,
    private val userPreferences: UserPreferences
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        // Check if user is logged in
        val token = userPreferences.getAccessToken().first()
        if (token == null) {
            return Result.success()
        }

        return try {
            // Perform sync
            val lastSync = userPreferences.getLastSyncTime().first()
            val result = syncRepository.sync(since = lastSync)

            if (result.isSuccess) {
                // Update last sync time
                userPreferences.saveLastSyncTime(System.currentTimeMillis())
                Result.success()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
```

### 7. Compose UI - Dashboard Screen

**DashboardScreen.kt:**

```kotlin
package com.ziggyai.mobile.ui.screens.dashboard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ZiggyAI") }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Portfolio Summary
            item {
                PortfolioCard(portfolio = uiState.portfolio)
            }

            // Market Watchlist
            item {
                Text(
                    "Watchlist",
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.padding(16.dp)
                )
            }

            items(uiState.quotes) { quote ->
                QuoteCard(quote = quote)
            }

            // Recent Signals
            item {
                Text(
                    "Trading Signals",
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.padding(16.dp)
                )
            }

            items(uiState.signals) { signal ->
                SignalCard(signal = signal)
            }
        }
    }
}
```

### 8. Push Notifications

**ZiggyFirebaseMessagingService.kt:**

```kotlin
package com.ziggyai.mobile.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.ziggyai.mobile.R
import com.ziggyai.mobile.data.preferences.UserPreferences
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class ZiggyFirebaseMessagingService : FirebaseMessagingService() {

    @Inject
    lateinit var userPreferences: UserPreferences

    override fun onMessageReceived(message: RemoteMessage) {
        createNotificationChannel()

        when (message.data["type"]) {
            "alert_triggered" -> showAlertNotification(message.data)
            "signal_new" -> showSignalNotification(message.data)
            "news" -> showNewsNotification(message.data)
        }
    }

    override fun onNewToken(token: String) {
        // Save token and update on server
        CoroutineScope(Dispatchers.IO).launch {
            userPreferences.savePushToken(token)
            // TODO: Update token on server via API
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                "ziggy_alerts",
                "ZiggyAI Alerts",
                NotificationManager.IMPORTANCE_HIGH
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun showAlertNotification(data: Map<String, String>) {
        val notification = NotificationCompat.Builder(this, "ziggy_alerts")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Price Alert Triggered")
            .setContentText(data["message"])
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(1, notification)
    }

    private fun showSignalNotification(data: Map<String, String>) {
        // Similar implementation for signals
    }

    private fun showNewsNotification(data: Map<String, String>) {
        // Similar implementation for news
    }
}
```

## Security Best Practices

### 1. Token Storage

Use EncryptedSharedPreferences:

```kotlin
val encryptedPrefs = EncryptedSharedPreferences.create(
    context,
    "ziggy_secure_prefs",
    MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build(),
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
```

### 2. Network Security

**res/xml/network_security_config.xml:**

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.ziggyai.com</domain>
        <pin-set>
            <pin digest="SHA-256">base64EncodedPin==</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

## Testing

### Unit Tests

```kotlin
@Test
fun `test market repository returns cached data first`() = runTest {
    // Arrange
    val mockApi = mock<ZiggyApiService>()
    val mockDao = mock<QuoteDao>()
    val repository = MarketRepository(mockApi, mockDao)

    // Act
    repository.getQuotes(listOf("AAPL")).collect { result ->
        // Assert
        assertTrue(result.isSuccess)
    }
}
```

### UI Tests

```kotlin
@Test
fun dashboard_displaysPortfolio() {
    composeTestRule.setContent {
        DashboardScreen()
    }

    composeTestRule
        .onNodeWithText("Portfolio")
        .assertIsDisplayed()
}
```

## Deployment

### Build Release APK

```bash
./gradlew assembleRelease
```

### Build App Bundle

```bash
./gradlew bundleRelease
```

The release build will be in `app/build/outputs/`.

## Next Steps

1. **Set up Firebase Project** for push notifications
2. **Configure ProGuard** for code obfuscation
3. **Set up Crashlytics** for error tracking
4. **Implement Analytics** for user tracking
5. **Add Biometric Authentication** for enhanced security
6. **Implement Widget** for quick market overview
7. **Add Wear OS Support** for smartwatch integration

## Resources

- [Android Developers Documentation](https://developer.android.com)
- [Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [Kotlin Documentation](https://kotlinlang.org/docs/home.html)
- [ZiggyAI Mobile API Documentation](./MOBILE_API_GUIDE.md)

## Support

For development support or questions:

- Create an issue on GitHub
- Email: dev-support@ziggyai.com
- Discord: https://discord.gg/ziggyai
