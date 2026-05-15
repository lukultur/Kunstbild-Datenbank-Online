import streamlit as st


def lade_css():
    st.markdown(
        """
        <style>

        .fixed-image-box {
            width: 100%;
            height: 210px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.65rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            display: block;
        }

        .kunst-title {
            height: 2.6em;
            overflow: hidden;
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.3;
            margin-top: 0.45rem;
            margin-bottom: 0.35rem;
        }

        .kunst-meta-kompakt {
            min-height: 2.4em;
            font-size: 0.82rem;
            line-height: 1.35;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.75rem;
            border-radius: 12px;
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 2.2rem;
            border-radius: 8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )