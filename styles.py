import streamlit as st


def lade_css():

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }

        section[data-testid="stSidebar"] {
            background-color: #262730;
        }

        h1, h2, h3, h4, h5, h6,
        p, label, span, div {
            color: #f5f5f5;
        }

        .fixed-image-box {
            width: 100%;
            height: 260px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 0.75rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .kunst-title {
            height: 3.1em;
            overflow: hidden;
            font-size: 1.1rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.6rem;
            margin-bottom: 0.4rem;
            color: #ffffff;
        }

        .kunst-meta {
            min-height: 5.2em;
            font-size: 0.92rem;
            line-height: 1.45;
            color: #e6e6e6;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 0.8rem;
        }

        @media (max-width: 768px) {

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .fixed-image-box {
                height: 220px;
            }

            .kunst-title {
                font-size: 1rem;
                height: auto;
            }

            .kunst-meta {
                font-size: 0.85rem;
                min-height: auto;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )