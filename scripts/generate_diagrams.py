#!/usr/bin/env python3
"""
GreenBuy Diagram Generator
Tự động tạo diagram images từ Mermaid code
"""

import os
import base64
import requests
from pathlib import Path

def encode_mermaid(mermaid_code: str) -> str:
    """Encode Mermaid code to base64"""
    return base64.b64encode(mermaid_code.encode()).decode()

def generate_image(mermaid_code: str, filename: str) -> bool:
    """Generate image from Mermaid code"""
    try:
        # Create output directory
        output_dir = Path("docs/diagram-images")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Encode mermaid code
        encoded = encode_mermaid(mermaid_code)
        
        # Generate URL
        url = f"https://mermaid.ink/img/{encoded}?type=png&theme=default"
        
        # Download image
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save image
        output_path = output_dir / filename
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating {filename}: {e}")
        return False

def main():
    """Generate all diagrams"""
    print("🛒 GreenBuy Diagram Generator")
    
    # System Architecture
    system_arch = """
graph TB
    subgraph "Client Layer"
        A[Mobile App] 
        B[Web App]
    end
    
    subgraph "API Gateway"
        D[FastAPI Server]
        E[WebSocket Server]
    end
    
    subgraph "Business Logic"
        F[User Management]
        G[Product Management]
        H[Order Management]
    end
    
    subgraph "Data Layer"
        K[(PostgreSQL + TimescaleDB)]
    end
    
    A --> D
    B --> D
    D --> F
    D --> G
    D --> H
    F --> K
    G --> K
    H --> K
"""
    
    # Database ERD
    database_erd = """
erDiagram
    users ||--o{ orders : places
    users ||--|| shop : owns
    shop ||--o{ products : sells
    products ||--o{ attributes : has
    attributes ||--o{ cart_items : selected_in
    cart ||--o{ cart_items : contains
    orders ||--o{ order_items : contains
    payments ||--o{ orders : paid_by
"""
    
    # Generate diagrams
    diagrams = {
        "system-architecture.png": system_arch,
        "database-erd.png": database_erd
    }
    
    success_count = 0
    for filename, mermaid_code in diagrams.items():
        if generate_image(mermaid_code, filename):
            success_count += 1
    
    print(f"\n📊 Generated {success_count}/{len(diagrams)} diagrams successfully!")

if __name__ == "__main__":
    main() 