import streamlit as st


def lade_css():

    st.markdown(
        """
        <style>

        .fixed-image-box {
            width: 100%;
            height: 260px;

            display: flex;
            align-items: center;
            justify-content: center;

            background: #f7f7f7;

            border-radius: 8px;
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

            font-size: 1.15rem;
            font-weight: 700;

            line-height: 1.25;

            margin-bottom: 0.35rem;
        }

        .kunst-meta {
            min-height: 5.2em;
            font-size: 0.95rem;
        }

        .stButton > button {
            width: 100%;
        }

        .stDownloadButton > button {
            width: 100%;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )