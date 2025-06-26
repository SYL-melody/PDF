import fitz  # PyMuPDF
import difflib
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import io
import imagehash

# ========== 文本和图像提取/比对功能 ==========

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    texts = [page.get_text() for page in doc]
    doc.close()
    return texts

def extract_images(page):
    """从 PDF 页面中提取图像并返回 PIL Image 对象列表"""
    images = []
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        images.append((img_index, image, xref))
    return images

def compare_images(images1, images2, page_number, report_lines):
    """比较两页的图像列表并返回差异描述"""
    if len(images1) != len(images2):
        report_lines.append(f"Page {page_number + 1} has different number of images: {len(images1)} vs {len(images2)}")
        return True

    diff_found = False
    for i, (idx1, img1, _) in enumerate(images1):
        _, img2, _ = images2[i]
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        if hash1 - hash2 > 5:
            report_lines.append(f"Page {page_number + 1}, image {i + 1} differs (phash difference: {hash1 - hash2})")
            diff_found = True
    return diff_found

# ========== PDF 比对核心函数 ==========

def highlight_and_report(pdf_path1, pdf_path2, output_path, report_path):
    doc1 = fitz.open(pdf_path1)
    doc2 = fitz.open(pdf_path2)
    out_doc = fitz.open()

    max_pages = max(len(doc1), len(doc2))
    report_lines = []

    for i in range(max_pages):
        report_lines.append(f"\n--- Page {i + 1} ---")

        if i >= len(doc1):
            report_lines.append("Only in file 2 (extra page).")
            out_doc.insert_pdf(doc2, from_page=i, to_page=i)
            continue
        elif i >= len(doc2):
            report_lines.append("Only in file 1 (extra page).")
            out_doc.insert_pdf(doc1, from_page=i, to_page=i)
            continue

        page1 = doc1[i]
        page2 = doc2[i]

        text1 = page1.get_text()
        text2 = page2.get_text()

        words1 = text1.split()
        words2 = text2.split()

        matcher = difflib.SequenceMatcher(None, words1, words2)
        diffs = matcher.get_opcodes()

        new_page = out_doc.new_page(width=page2.rect.width, height=page2.rect.height)
        new_page.show_pdf_page(new_page.rect, doc2, i)

        word_boxes = page2.get_text("words")
        for tag, i1, i2, j1, j2 in diffs:
            if tag != 'equal':
                for w in range(j1, j2):
                    if w < len(word_boxes):
                        x0, y0, x1, y1, word, *_ = word_boxes[w]
                        rect = fitz.Rect(x0, y0, x1, y1)
                        new_page.draw_rect(rect, color=(1, 0, 0), width=0.7)
                diff_text = f"Text difference [{tag}] - file1: {' '.join(words1[i1:i2])} | file2: {' '.join(words2[j1:j2])}"
                report_lines.append(diff_text)

        # 图像比对
        images1 = extract_images(page1)
        images2 = extract_images(page2)
        if compare_images(images1, images2, i, report_lines):
            new_page.insert_text((50, 50), "Images differ!", fontsize=12, color=(1, 0, 0))

    out_doc.save(output_path)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    doc1.close()
    doc2.close()
    out_doc.close()

    return output_path, report_path

# ========== 图形界面（GUI） ==========

def run_gui():
    def select_file(entry):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def compare_files():
        file1 = entry1.get()
        file2 = entry2.get()

        if not file1 or not file2:
            messagebox.showerror("Error", "Please select two PDF files.")
            return

        output_file = "diff_output.pdf"
        report_file = "diff_report.txt"
        try:
            output_path, report_path = highlight_and_report(file1, file2, output_file, report_file)
            messagebox.showinfo("Done", f"Comparison complete!\n\nOutput PDF: {output_path}\nReport: {report_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed:\n{str(e)}")

    root = tk.Tk()
    root.title("PDF 文件比对工具")
    root.geometry("500x400")

    tk.Label(root, text="PDF 文件 1:").pack(pady=5)
    entry1 = tk.Entry(root, width=50)
    entry1.pack()
    tk.Button(root, text="选择文件", command=lambda: select_file(entry1)).pack()

    tk.Label(root, text="PDF 文件 2:").pack(pady=5)
    entry2 = tk.Entry(root, width=50)
    entry2.pack()
    tk.Button(root, text="选择文件", command=lambda: select_file(entry2)).pack()

    tk.Button(root, text="开始比对", command=compare_files, bg="green", fg="white").pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
