import streamlit as st
import pandas as pd
import os
import io
from PIL import Image
from google import genai

# Tên file cố định lưu trên server
EXCEL_FILE = "dulieu_moinhat.xlsx"

st.set_page_config(page_title="Nhận diện bảng biểu AI", layout="wide")
st.title("📸 Ứng dụng Quét Bảng (Sử dụng AI Gemini)")

# Lấy API Key từ Sidebar
st.sidebar.header("⚙️ Cấu hình AI")
api_key = st.sidebar.text_input("Nhập Google Gemini API Key:", type="password")
st.sidebar.markdown("""
**Tại sao dùng Gemini?**
Công nghệ cũ không đọc được bảng có nền xám và thiếu đường kẻ ngang. AI Gemini giải quyết triệt để vấn đề này với độ chính xác cực cao.
[👉 Bấm vào đây để lấy API Key miễn phí](https://aistudio.google.com/app/apikey)
""")

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
        image = Image.open(img_file)
        st.image(image, caption="Ảnh đã tải lên", use_container_width=True)
        
        if st.button("🚀 Bắt đầu quét", type="primary"):
            if not api_key:
                st.error("⚠️ Vui lòng dán Gemini API Key ở thanh bên trái trước khi quét!")
            else:
                with st.spinner("🤖 AI đang phân tích bảng biểu... Vui lòng đợi (khoảng 10 giây)!"):
                    try:
                        # Khởi tạo AI
                        client = genai.Client(api_key=api_key)
                        
                        # Lệnh yêu cầu AI xử lý ảnh
                        prompt = """
                        Hãy trích xuất dữ liệu từ bảng chính trong bức ảnh này và trả về dưới dạng CSV.
                        Yêu cầu BẮT BUỘC:
                        1. Chỉ lấy bảng lớn phía trên (gồm các cột Lot No, Maximum Load...). Bỏ qua phần bảng nhỏ 'Hien tuong', 'Vi tri' ở dưới.
                        2. Cột đầu tiên (chứa các số 156, 157...) không có tiêu đề, hãy đặt tên là 'STT'.
                        3. Chỉ trả về chuỗi CSV thô, phân cách bằng dấu phẩy (,). Tuyệt đối KHÔNG bọc trong markdown (không dùng ```csv).
                        4. Đọc thật chính xác các con số thập phân. Nếu ô trống (như cột Average Load) thì để trống.
                        """
                        
                        # Gửi ảnh cho AI Gemini 2.5 Flash
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[image, prompt]
                        )
                        
                        csv_data = response.text.strip()
                        
                        # Xử lý dọn dẹp nếu AI lỡ trả về định dạng markdown
                        if csv_data.startswith("```"):
                            csv_data = csv_data.split("\n", 1)[1]
                        if csv_data.endswith("```"):
                            csv_data = csv_data.rsplit("\n", 1)[0]
                            
                        # Chuyển dữ liệu CSV thành Bảng (DataFrame) và lưu ra Excel
                        df = pd.read_csv(io.StringIO(csv_data))
                        df.to_excel(EXCEL_FILE, index=False)
                        
                        st.success("✅ Đã quét xong! Hãy mở Tab 2 trên máy tính để lấy dữ liệu.")
                    except Exception as e:
                        st.error(f"❌ Có lỗi xảy ra: {e}")

# ==========================================
# TAB 2: DÀNH CHO MÁY TÍNH (LẤY DỮ LIỆU)
# ==========================================
with tab2:
    st.header("Dữ liệu bảng biểu mới nhất")
    
    if st.button("🔄 Tải lại dữ liệu mới nhất"):
        st.rerun()
        
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            st.success(f"🎉 Đã tải dữ liệu thành công!")
            
            # Hiển thị bảng ra màn hình
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
        st.info("⏳ Chưa có dữ liệu nào. Hãy dùng điện thoại quét ảnh ở Tab 1 trước.")
