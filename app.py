import streamlit as st
import pandas as pd
import os
from img2table.document import Image
from img2table.ocr import TesseractOCR

# Tên file cố định lưu trên server của Streamlit Cloud
EXCEL_FILE = "dulieu_moinhat.xlsx"
TEMP_IMAGE = "temp_image.png"

st.set_page_config(page_title="Nhận diện bảng biểu", layout="wide")
st.title("📸 Ứng dụng Quét và Lấy dữ liệu Bảng")

tab1, tab2 = st.tabs(["📱 Tab 1: Điện thoại (Quét ảnh)", "💻 Tab 2: Máy tính (Lấy dữ liệu)"])

# ==========================================
# TAB 1: DÀNH CHO ĐIỆN THOẠI (QUÉT ẢNH)
# ==========================================
with tab1:
    st.header("Chụp hoặc tải ảnh chứa bảng biểu")
    
    upload_option = st.radio("Chọn phương thức:", ("Tải ảnh từ máy", "Chụp ảnh từ Camera"))
    
    img_file = None
    if upload_option == "Tải ảnh từ máy":
        img_file = st.file_uploader("Chọn ảnh", type=["png", "jpg", "jpeg"])
    else:
        img_file = st.camera_input("Chụp ảnh")

    if img_file is not None:
        st.image(img_file, caption="Ảnh đã tải lên", use_container_width=True)
        
        if st.button("🚀 Bắt đầu quét", type="primary"):
            with st.spinner("Đang xử lý ảnh và nhận diện bảng biểu... Vui lòng đợi!"):
                try:
                    # Lưu ảnh tạm thời xuống server
                    with open(TEMP_IMAGE, "wb") as f:
                        f.write(img_file.getbuffer())
                    
                    # Khởi tạo OCR Tesseract với tiếng Việt
                    ocr = TesseractOCR(n_threads=1, lang="vie")
                    
                    # Đọc ảnh bằng img2table
                    doc = Image(TEMP_IMAGE)
                    
                    # CẬP NHẬT QUAN TRỌNG Ở ĐÂY:
                    # Bật borderless_tables=True và implicit_rows=True
                    doc.to_xlsx(dest=EXCEL_FILE,
                                ocr=ocr,
                                implicit_rows=True,      # Bật nhận diện hàng không có đường kẻ
                                borderless_tables=True,  # Bật nhận diện bảng không có viền
                                min_confidence=50)
                    
                    st.success("✅ Đã quét xong! Hãy mở Tab 2 trên máy tính để lấy dữ liệu.")
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra trong quá trình quét: {e}")

# ==========================================
# TAB 2: DÀNH CHO MÁY TÍNH (LẤY DỮ LIỆU)
# ==========================================
with tab2:
    st.header("Dữ liệu bảng biểu mới nhất")
    
    # Nút tải lại trang để cập nhật file mới nhất
    if st.button("🔄 Tải lại dữ liệu mới nhất"):
        st.rerun()
        
    # Kiểm tra xem file đã tồn tại trên server chưa
    if os.path.exists(EXCEL_FILE):
        try:
            xls = pd.ExcelFile(EXCEL_FILE)
            sheet_names = xls.sheet_names
            
            if not sheet_names:
                st.warning("⚠️ Không tìm thấy bảng nào trong ảnh vừa quét. Hãy thử chụp lại ảnh rõ nét hơn và vuông góc hơn.")
            else:
                st.success(f"🎉 Tìm thấy {len(sheet_names)} bảng!")
                
                for sheet in sheet_names:
                    st.subheader(f"Bảng: {sheet}")
                    df = pd.read_excel(xls, sheet_name=sheet)
                    
                    # Xóa các cột/hàng trống hoàn toàn (nếu có) do nhiễu
                    df.dropna(how='all', inplace=True)
                    df.dropna(axis=1, how='all', inplace=True)
                    
                    # Hiển thị dataframe
                    st.dataframe(df, use_container_width=True)
                
                st.markdown("---")
                with open(EXCEL_FILE, "rb") as f:
                    st.download_button(
                        label="⬇️ Tải file Excel này về máy",
                        data=f,
                        file_name="ket_qua_quet_bang.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error(f"❌ Không thể đọc file dữ liệu: {e}")
    else:
        st.info("⏳ Chưa có dữ liệu nào. Hãy dùng điện thoại truy cập web này và quét ảnh ở Tab 1 trước.")
