from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 50, "The Future of AI Agents")
    
    # Body Content
    c.setFont("Helvetica", 12)
    text = """
    This is a sample PDF file created for IPL Teams.
    """
    
    y_position = height - 100
    for line in text.strip().split('\n'):
        c.drawString(100, y_position, line.strip())
        y_position -= 20
        
    c.save()
    print(f"PDF created: {filename}")

if __name__ == "__main__":
    create_sample_pdf("sample_rag_test.pdf")
