from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 50, "SAMPLE PDF : CHESS PIECES")
    
    # Body Content
    c.setFont("Helvetica", 12)
    text = """
    This is a sample PDF file created for CHESS Pieces.
    1. King: Moves one square in any direction (horizontally, vertically, or diagonally).
    2. Queen: Moves any number of squares in any direction (horizontally, vertically, or diagonally).
    3. Rook: Moves any number of squares in straight lines (horizontally or vertically).
    4. Bishop: Moves any number of squares diagonally.
    5. Knight: Moves in an L-shape: two squares in one direction and then one square perpendicular; can jump over pieces.
    6. Pawn: Moves forward one square (or two squares from its starting rank), captures one square diagonally forward, and can promote on reaching the last rank.
    """
    
    y_position = height - 100
    for line in text.strip().split('\n'):
        c.drawString(100, y_position, line.strip())
        y_position -= 20
        
    c.save()
    print(f"PDF created: {filename}")

if __name__ == "__main__":
    create_sample_pdf("sample_rag_chess.pdf")
