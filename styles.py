import streamlit as st


def lade_css():
    st.markdown(
        """
        <style>

        .stApp {
            background-color: #050816;
            color: #f5f5f5;
        }

        section[data-testid="stSidebar"] {
            background-color: #262730;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        h1, h2, h3, h4 {
            color: #fff5ee;
        }

        .kunst-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.2rem;
        }

        .kunst-card {
            background: #0c1224;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            overflow: hidden;
            padding: 1rem;
            height: 100%;
        }

        .kunstbild-wrapper {
            width: 100%;
            height: 320px;
            background: #0a1020;
            border-radius: 14px;
            overflow: hidden;

            display: flex;
            align-items: center;
            justify-content: center;

            margin-bottom: 1rem;
        }

        .kunstbild-wrapper img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            display: block;
        }

        .kunst-title {
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.3;
            color: white;

            min-height: 3.2rem;
            margin-bottom: 0.6rem;

            overflow: hidden;
        }

        .kunst-meta-kompakt {
            color: #d0d0d0;
            font-size: 0.95rem;
            line-height: 1.45;

            min-height: 4rem;
            margin-bottom: 1rem;
        }

        .stButton button {
            border-radius: 10px;
        }

        .stDownloadButton button {
            border-radius: 10px;
        }

        div[data-testid="stPopover"] button {
            border-radius: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )