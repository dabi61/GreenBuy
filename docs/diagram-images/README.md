# 📊 GreenBuy Diagram Images

## 🖼️ Cách tạo hình ảnh từ Mermaid diagrams

### **1. Sử dụng Mermaid Live Editor**

1. Truy cập: https://mermaid.live/
2. Copy code Mermaid từ file `architecture-diagram.md`
3. Paste vào editor
4. Export thành PNG/SVG

### **2. Sử dụng GitHub**

1. Tạo file `.md` với Mermaid code
2. Push lên GitHub
3. GitHub tự động render Mermaid
4. Screenshot hoặc sử dụng browser dev tools

### **3. Sử dụng Node.js Mermaid CLI**

```bash
# Cài đặt mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Export diagram
mmdc -i input.mmd -o output.png
```

### **4. Sử dụng Python**

```python
import requests
import json

def generate_mermaid_image(mermaid_code, output_file):
    url = "https://mermaid.ink/img/"
    
    # Encode mermaid code
    import base64
    encoded = base64.b64encode(mermaid_code.encode()).decode()
    
    # Generate URL
    image_url = f"{url}{encoded}"
    
    # Download image
    response = requests.get(image_url)
    with open(output_file, 'wb') as f:
        f.write(response.content)

# Example usage
mermaid_code = """
graph TB
    A[User] --> B[API]
    B --> C[Database]
"""
generate_mermaid_image(mermaid_code, "diagram.png")
```

## 📋 Danh sách diagrams cần tạo

### **1. System Architecture**
- **File**: `system-architecture.png`
- **Size**: 1920x1080
- **Format**: PNG/SVG
- **Usage**: Presentations, documentation

### **2. Database ERD**
- **File**: `database-erd.png`
- **Size**: 1600x1200
- **Format**: PNG/SVG
- **Usage**: Database documentation

### **3. API Flow**
- **File**: `api-flow.png`
- **Size**: 1400x800
- **Format**: PNG/SVG
- **Usage**: API documentation

### **4. User Journey**
- **File**: `user-journey.png`
- **Size**: 1200x900
- **Format**: PNG/SVG
- **Usage**: UX documentation

### **5. Security Architecture**
- **File**: `security-architecture.png`
- **Size**: 1600x1000
- **Format**: PNG/SVG
- **Usage**: Security reviews

### **6. Deployment Architecture**
- **File**: `deployment-architecture.png`
- **Size**: 1800x1200
- **Format**: PNG/SVG
- **Usage**: DevOps documentation

### **7. Chat System**
- **File**: `chat-system.png`
- **Size**: 1400x900
- **Format**: PNG/SVG
- **Usage**: Real-time features

### **8. Payment Flow**
- **File**: `payment-flow.png`
- **Size**: 1200x800
- **Format**: PNG/SVG
- **Usage**: Payment integration

### **9. Order Status Flow**
- **File**: `order-status-flow.png`
- **Size**: 1000x600
- **Format**: PNG/SVG
- **Usage**: Order management

### **10. Product Approval Flow**
- **File**: `product-approval-flow.png`
- **Size**: 1200x700
- **Format**: PNG/SVG
- **Usage**: Admin workflows

## 🎨 Design Guidelines

### **Colors**
- **Primary**: #2563eb (Blue)
- **Secondary**: #10b981 (Green)
- **Warning**: #f59e0b (Yellow)
- **Error**: #ef4444 (Red)
- **Success**: #22c55e (Green)
- **Background**: #ffffff (White)
- **Text**: #1f2937 (Dark Gray)

### **Typography**
- **Font**: Inter, Arial, sans-serif
- **Size**: 12-16px for text, 18-24px for titles
- **Weight**: Normal (400), Bold (700)

### **Layout**
- **Padding**: 20px minimum
- **Margins**: 10px between elements
- **Border Radius**: 8px for boxes
- **Shadows**: Subtle drop shadows

## 📁 File Structure

```
docs/
├── diagram-images/
│   ├── README.md
│   ├── system-architecture.png
│   ├── database-erd.png
│   ├── api-flow.png
│   ├── user-journey.png
│   ├── security-architecture.png
│   ├── deployment-architecture.png
│   ├── chat-system.png
│   ├── payment-flow.png
│   ├── order-status-flow.png
│   └── product-approval-flow.png
└── architecture-diagram.md
```

## 🚀 Quick Export Script

```bash
#!/bin/bash
# quick-export-diagrams.sh

# Tạo thư mục nếu chưa có
mkdir -p docs/diagram-images

# Danh sách diagrams
diagrams=(
    "system-architecture"
    "database-erd"
    "api-flow"
    "user-journey"
    "security-architecture"
    "deployment-architecture"
    "chat-system"
    "payment-flow"
    "order-status-flow"
    "product-approval-flow"
)

# Export từng diagram
for diagram in "${diagrams[@]}"; do
    echo "Exporting $diagram..."
    # Sử dụng mermaid-cli hoặc curl
    # mmdc -i "$diagram.mmd" -o "docs/diagram-images/$diagram.png"
done

echo "All diagrams exported successfully!"
```

## 📝 Usage Examples

### **1. README.md**
```markdown
![System Architecture](docs/diagram-images/system-architecture.png)
```

### **2. Documentation**
```html
<img src="docs/diagram-images/database-erd.png" alt="Database ERD" width="800">
```

### **3. Presentations**
- Import PNG files vào PowerPoint/Keynote
- Use SVG for web presentations
- Maintain aspect ratio

### **4. Technical Documentation**
```asciidoc
image::docs/diagram-images/api-flow.png[API Flow Diagram,800,600]
```

## 🔧 Automation

### **GitHub Actions Workflow**
```yaml
name: Generate Diagrams
on:
  push:
    paths: ['docs/architecture-diagram.md']

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: npm install -g @mermaid-js/mermaid-cli
      - run: |
          # Generate diagrams from markdown
          # Add your diagram generation logic here
```

---

**Lưu ý**: Đảm bảo tất cả diagram images được tạo với chất lượng cao và có thể sử dụng cho nhiều mục đích khác nhau từ documentation đến presentations. 