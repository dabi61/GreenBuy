# 📊 Sử dụng Diagrams trong GreenBuy Documentation

## 🎯 Mục đích

Các diagram này được tạo để:
- **Giải thích kiến trúc hệ thống** cho developers mới
- **Trình bày cho stakeholders** về tính năng và workflow
- **Hướng dẫn implementation** cho team development
- **Documentation** cho API và database design

## 📋 Danh sách Diagrams

### **1. System Architecture** 
- **File**: `system-architecture.png`
- **Mô tả**: Tổng quan kiến trúc hệ thống GreenBuy
- **Sử dụng**: README, Technical Documentation, Presentations

### **2. Database ERD**
- **File**: `database-erd.png`
- **Mô tả**: Entity Relationship Diagram của database
- **Sử dụng**: Database Documentation, Development Guide

### **3. API Flow**
- **File**: `api-flow.png`
- **Mô tả**: Luồng tương tác giữa client và API
- **Sử dụng**: API Documentation, Integration Guide

### **4. User Journey**
- **File**: `user-journey.png`
- **Mô tả**: User experience flow từ đăng ký đến hoàn thành đơn hàng
- **Sử dụng**: UX Documentation, Product Requirements

### **5. Security Architecture**
- **File**: `security-architecture.png`
- **Mô tả**: Các lớp bảo mật của hệ thống
- **Sử dụng**: Security Reviews, Compliance Documentation

### **6. Deployment Architecture**
- **File**: `deployment-architecture.png`
- **Mô tả**: Kiến trúc triển khai và infrastructure
- **Sử dụng**: DevOps Documentation, Deployment Guide

### **7. Chat System**
- **File**: `chat-system.png`
- **Mô tả**: Kiến trúc hệ thống chat real-time
- **Sử dụng**: Real-time Features Documentation

### **8. Payment Flow**
- **File**: `payment-flow.png`
- **Mô tả**: Luồng xử lý thanh toán
- **Sử dụng**: Payment Integration Guide

### **9. Order Status Flow**
- **File**: `order-status-flow.png`
- **Mô tả**: State machine của đơn hàng
- **Sử dụng**: Order Management Documentation

### **10. Product Approval Flow**
- **File**: `product-approval-flow.png`
- **Mô tả**: Workflow duyệt sản phẩm
- **Sử dụng**: Admin Workflow Documentation

## 📝 Cách sử dụng trong Documentation

### **1. Markdown Files**

```markdown
# System Architecture

![GreenBuy System Architecture](docs/diagram-images/system-architecture.png)

Hệ thống GreenBuy được xây dựng với kiến trúc microservices...
```

### **2. HTML Documentation**

```html
<div class="diagram-container">
    <img src="docs/diagram-images/database-erd.png" 
         alt="Database Entity Relationship Diagram"
         class="diagram-image"
         width="800">
    <p class="diagram-caption">Database ERD - Mối quan hệ giữa các bảng</p>
</div>
```

### **3. Presentations (PowerPoint/Keynote)**

1. Import PNG files vào slide
2. Maintain aspect ratio
3. Add captions and explanations
4. Use consistent styling

### **4. Technical Documentation**

```asciidoc
[source,mermaid]
----
graph TB
    A[User] --> B[API]
    B --> C[Database]
----

image::docs/diagram-images/api-flow.png[API Flow,800,600]
```

## 🎨 Styling Guidelines

### **CSS cho Web Documentation**

```css
.diagram-container {
    margin: 2rem 0;
    text-align: center;
}

.diagram-image {
    max-width: 100%;
    height: auto;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.diagram-caption {
    margin-top: 1rem;
    font-size: 0.875rem;
    color: #6b7280;
    font-style: italic;
}
```

### **Print-friendly Styling**

```css
@media print {
    .diagram-image {
        max-width: 90%;
        page-break-inside: avoid;
    }
}
```

## 📱 Responsive Design

### **Mobile-friendly Images**

```html
<picture>
    <source media="(min-width: 768px)" 
            srcset="docs/diagram-images/system-architecture.png">
    <source media="(max-width: 767px)" 
            srcset="docs/diagram-images/system-architecture-mobile.png">
    <img src="docs/diagram-images/system-architecture.png" 
         alt="System Architecture"
         class="diagram-image">
</picture>
```

## 🔄 Version Control

### **Naming Convention**

```
diagram-name-v1.0.png
diagram-name-v1.1.png
diagram-name-current.png
```

### **Git LFS (Large File Storage)**

```bash
# .gitattributes
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.svg filter=lfs diff=lfs merge=lfs -text
```

## 🚀 Automation

### **Auto-generate từ Mermaid**

```bash
# Chạy script generate diagrams
python scripts/generate_diagrams.py

# Hoặc sử dụng GitHub Actions
# .github/workflows/generate-diagrams.yml
```

### **Continuous Integration**

```yaml
name: Generate Diagrams
on:
  push:
    paths: ['docs/architecture-diagram.md']
  pull_request:
    paths: ['docs/architecture-diagram.md']

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install requests
      - run: python scripts/generate_diagrams.py
      - run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/diagram-images/
          git commit -m "Auto-generate diagrams" || exit 0
          git push
```

## 📊 Quality Assurance

### **Checklist trước khi sử dụng**

- [ ] Diagram có độ phân giải cao (min 800px width)
- [ ] Text readable và không bị cắt
- [ ] Colors consistent với brand guidelines
- [ ] File size optimized (< 500KB cho PNG)
- [ ] Alt text descriptive
- [ ] Caption explanatory

### **Accessibility**

```html
<img src="docs/diagram-images/database-erd.png" 
     alt="Database Entity Relationship Diagram showing relationships between Users, Products, Orders, and Payments tables"
     aria-describedby="erd-description">
<div id="erd-description" class="sr-only">
    ERD showing Users can have multiple Orders, Products belong to Shops, 
    and Orders contain multiple Order Items linked to Product Attributes.
</div>
```

## 📈 Analytics

### **Track Diagram Usage**

```javascript
// Track diagram views
document.querySelectorAll('.diagram-image').forEach(img => {
    img.addEventListener('load', () => {
        analytics.track('diagram_viewed', {
            diagram_name: img.src.split('/').pop(),
            page_url: window.location.href
        });
    });
});
```

---

## 🎯 Best Practices

1. **Consistency**: Sử dụng cùng style cho tất cả diagrams
2. **Clarity**: Đảm bảo diagram dễ hiểu và rõ ràng
3. **Accessibility**: Thêm alt text và descriptions
4. **Performance**: Optimize file size
5. **Versioning**: Track changes và updates
6. **Documentation**: Giải thích ý nghĩa của diagram

## 📞 Support

Nếu cần hỗ trợ tạo hoặc cập nhật diagrams:

1. **Technical Issues**: Tạo issue trên GitHub
2. **Design Requests**: Contact design team
3. **Content Updates**: Submit pull request
4. **Automation**: Check CI/CD pipeline

---

**Lưu ý**: Tất cả diagrams được tạo bằng Mermaid và có thể được cập nhật tự động thông qua CI/CD pipeline. 