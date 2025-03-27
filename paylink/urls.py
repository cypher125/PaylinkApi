"""
URL configuration for paylink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from django.http import JsonResponse, HttpResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

def api_root(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PayLink API</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #0070f3;
                --primary-dark: #0056b3;
                --secondary-color: #7928ca;
                --accent-color: #00d4ff;
                --text-color: #333;
                --text-light: #666;
                --background-light: #f8f9fa;
                --success-color: #0cce6b;
                --warning-color: #ff9800;
                --error-color: #ff4757;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                background: linear-gradient(135deg, var(--background-light), #fff);
                min-height: 100vh;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            
            .hero {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                padding: 60px 0 40px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }
            
            .logo {
                margin-bottom: 20px;
                width: 180px;
                height: auto;
            }
            
            h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 15px;
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                letter-spacing: -0.03em;
            }
            
            .subtitle {
                font-size: 1.25rem;
                color: var(--text-light);
                max-width: 600px;
                margin: 0 auto 30px;
            }
            
            .cta-button {
                display: inline-block;
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 14px 28px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(0, 112, 243, 0.15);
                margin-top: 10px;
            }
            
            .cta-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0, 112, 243, 0.25);
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 30px;
                margin: 60px 0;
            }
            
            .feature {
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                transition: transform 0.3s ease;
            }
            
            .feature:hover {
                transform: translateY(-5px);
            }
            
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 15px;
                color: var(--primary-color);
            }
            
            .feature h3 {
                font-size: 1.2rem;
                margin-bottom: 12px;
                color: var(--primary-color);
            }
            
            .docs-section {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                margin-bottom: 40px;
            }
            
            .docs-section h2 {
                font-size: 1.6rem;
                margin-bottom: 20px;
                color: var(--primary-color);
            }
            
            .version-badge {
                display: inline-block;
                background-color: var(--accent-color);
                color: white;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 0.8rem;
                margin-left: 10px;
                vertical-align: middle;
            }
            
            .footer {
                text-align: center;
                padding: 30px 0;
                color: var(--text-light);
                font-size: 0.9rem;
                border-top: 1px solid rgba(0,0,0,0.05);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <!-- Replace with your actual logo path -->
                <img src="/static/images/paylink-logo.png" alt="PayLink Logo" class="logo" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 30%22><text y=%2220%22 font-size=%2220%22 font-weight=%22bold%22 fill=%22%230070f3%22>PayLink</text></svg>'; this.style.height='60px';">
                
            <h1>Welcome to PayLink API</h1>
                <p class="subtitle">A modern API platform for financial transactions and bill payments with VTPass integration.</p>
                
                <a href="/api/docs/" class="cta-button">Explore API Documentation</a>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🔒</div>
                    <h3>Secure Authentication</h3>
                    <p>Our API uses JWT tokens for secure authentication and authorization, protecting sensitive financial data.</p>
                </div>
                
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <h3>Fast Transactions</h3>
                    <p>Process financial transactions quickly and reliably with our optimized API endpoints.</p>
                </div>
                
                <div class="feature">
                    <div class="feature-icon">📱</div>
                    <h3>VTPass Integration</h3>
                    <p>Seamlessly handle bill payments and airtime purchases through our VTPass integration.</p>
                </div>
            </div>
            
            <div class="docs-section">
                <h2>API Documentation <span class="version-badge">v1.0</span></h2>
                <p>Our comprehensive API documentation provides all the information you need to integrate with PayLink, including:</p>
                <ul style="margin-top: 15px; margin-left: 20px;">
                    <li>Authentication details</li>
                    <li>Available endpoints</li>
                    <li>Request/response formats</li>
                    <li>Error handling</li>
                    <li>Rate limits and best practices</li>
                </ul>
                <a href="/api/docs/" class="cta-button" style="margin-top: 20px;">View Documentation</a>
            </div>
            
            <div class="footer">
                <p>&copy; 2025 PayLink API. All rights reserved.</p>
                <p style="margin-top: 10px;">
                    <a href="#" style="color: var(--primary-color); text-decoration: none; margin: 0 10px;">Terms of Service</a>
                    <a href="#" style="color: var(--primary-color); text-decoration: none; margin: 0 10px;">Privacy Policy</a>
                    <a href="#" style="color: var(--primary-color); text-decoration: none; margin: 0 10px;">Contact</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content, content_type="text/html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('api/users/', include('users.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
