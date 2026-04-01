import streamlit as st
import pandas as pd
import os
import io
from PIL import Image
from google import genai

# ==========================================
# 1. LẤY API KEY TỪ "KÉT SẮT" CỦA STREAMLIT
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = ""

EXCEL_FILE = "dulieu_moinhat.xlsx"

# Cấu hình trang web
st.set_page_config(page_title="Nhận diện bảng biểu AI", layout="wide")

# ==========================================
# 2. XÓA BỎ CÁC THÀNH PHẦN THỪA CỦA STREAMLIT
# ==========================================
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;}    
            header {visibility: hidden;}    
            .stDeployButton {display:none;} 
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("📸 Ứng dụng Quét Bảng AI")

tab1, tab2 = st.tabs(["📱 Tab 1: Điện thoại (Quét ảnh)", "💻 Tab 2: Máy tính (Lấy dữ liệu)"])

# ==========================================
# TAB 1: DÀNH CHO ĐIỆN THOẠI (QUÉT ẢNH)
# ==========================================
with tab1:
    st.header("Tải lên các ảnh chứa bảng biểu")
    st.info("💡 Mẹo: Trên điện thoại, khi bấm nút 'Browse files' bên dưới, bạn có thể chọn 'Chụp ảnh' (Camera) để chụp trực tiếp, hoặc chọn nhiều ảnh cùng lúc từ Thư viện.")
    
    uploaded_files = st.file_uploader("Chọn một hoặc nhiều ảnh", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"📁 Đã chọn **{len(uploaded_files)}** ảnh.")
        
        if st.button("🚀 Bắt đầu quét tất cả", type="primary"):
            if not API_KEY:
                st.error("⚠️ Chưa cài đặt API Key trong Streamlit Secrets!")
            else:
                progress_bar = st.progress(0, text="Đang khởi động AI...")
                
                try:
                    client = genai.Client(api_key=API_KEY)
                    
                    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                        for i, img_file in enumerate(uploaded_files):
                            progress_bar.progress((i) / len(uploaded_files), text=f"Đang xử lý ảnh {i+1}/{len(uploaded_files)}...")
                            
                            image = Image.open(img_file)
                            
                            prompt = """
                            Hãy trích xuất dữ liệu từ bảng chính trong bức ảnh này và trả về dưới dạng CSV.
                            Yêu cầu BẮT BUỘC:
                            1. Chỉ lấy bảng lớn phía trên. Bỏ qua phần bảng nhỏ 'Hien tuong', 'Vi tri' ở dưới.
                            2. Cột đầu tiên không có tiêu đề, hãy đặt tên là 'STT'.
                            3. Chỉ trả về chuỗi CSV thô, phân cách bằng dấu phẩy (,). Tuyệt đối KHÔNG bọc trong markdown (không dùng ```csv).
                            4. Đọc thật chính xác các con số thập phân. Nếu ô trống thì để trống.
                            """
                            
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[image, prompt]
                            )
                            
                            csv_data = response.text.strip()
                            
                            if csv_data.startswith("```"):
                                csv_data = csv_data.split("\n", 1)[1]
                            if csv_data.endswith("```"):
                                csv_data = csv_data.rsplit("\n", 1)[0]
                                
                            df = pd.read_csv(io.StringIO(csv_data))
                            sheet_name = f"Trang_{i+1}"
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    progress_bar.progress(1.0, text="Hoàn tất!")
                    st.success(f"✅ Đã quét xong {len(uploaded_files)} ảnh và gộp thành 1 file Excel! Hãy mở Tab 2 trên máy tính để lấy dữ liệu.")
                
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {e}")

# ==========================================
# TAB 2: DÀNH CHO MÁY TÍNH (LẤY DỮ LIỆU)
# ==========================================
with tab2:
    st.header("Dữ liệu bảng biểu mới nhất")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Tải lại dữ liệu"):
            st.rerun()
            
    if os.path.exists(EXCEL_FILE):
        try:
            xls = pd.ExcelFile(EXCEL_FILE)
            sheet_names = xls.sheet_names
            
            st.success(f"🎉 Đã tải dữ liệu thành công! File Excel gồm {len(sheet_names)} trang (sheet).")
            
            with open(EXCEL_FILE, "rb") as f:
                st.download_button(
                    label="⬇️ Tải file Excel này về máy",
                    data=f,
                    file_name="ket_qua_quet_bang_gop.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            
            st.markdown("---")
            
            for sheet in sheet_names:
                st.subheader(f"📄 {sheet}")
                df = pd.read_excel(xls, sheet_name=sheet)
                st.dataframe(df, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Không thể đọc file dữ liệu: {e}")
    else:
        st.info("⏳ Chưa có dữ liệu nào. Hãy dùng điện thoại quét ảnh ở Tab 1 trước.")
