import streamlit as st


def lade_css():

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #0e1117;
            color: #f5f5f5;
        }

        .block-container {
            max-width: 1160px;
            padding-top: 2.2rem;
            padding-left: 1.6rem;
            padding-right: 1.6rem;
        }

        section[data-testid="stSidebar"] {
            background-color: #262730;
        }

        h1 {
            font-size: 2.15rem;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
        }

        h2, h3, h4, h5, h6,
        p, label, span, div {
            color: #f5f5f5;
        }

        .fixed-image-box {
            width: 100%;
            height: 205px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.55rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .kunst-title {
            height: 2.35em;
            overflow: hidden;
            font-size: 0.94rem;
            font-weight: 700;
            line-height: 1.22;
            margin-top: 0.35rem;
            margin-bottom: 0.25rem;
            color: #ffffff;
        }

        .kunst-meta-kompakt {
            min-height: 2.05em;
            font-size: 0.78rem;
            line-height: 1.3;
            color: #d1d5db;
            margin-bottom: 0.35rem;
        }

        .kunst-meta {
            min-height: 4em;
            font-size: 0.82rem;
            line-height: 1.35;
            color: #e6e6e6;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
            min-height: 2.05rem;
            font-size: 0.88rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 13px;
            padding: 0.55rem;
        }

        div[data-testid="column"] {
            padding-left: 0.32rem;
            padding-right: 0.32rem;
        }

        input, textarea, select {
            border-radius: 8px !important;
        }

        @media (max-width: 900px) {

            .block-container {
                padding-left: 0.9rem;
                padding-right: 0.9rem;
                padding-top: 1.5rem;
            }

            h1 {
                font-size: 1.75rem;
            }

            .fixed-image-box {
                height: 185px;
            }

            .kunst-title {
                font-size: 0.9rem;
                height: auto;
            }

            .kunst-meta-kompakt {
                font-size: 0.76rem;
                min-height: auto;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding: 0.5rem;
            }

        }

        @media (max-width: 640px) {

            .block-container {
                padding-left: 0.55rem;
                padding-right: 0.55rem;
                padding-top: 0.8rem;
            }

            h1 {
                font-size: 1.45rem;
                line-height: 1.15;
            }

            .fixed-image-box {
                height: 170px;
                border-radius: 11px;
                margin-bottom: 0.45rem;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding: 0.48rem;
                margin-bottom: 0.7rem;
                border-radius: 12px;
            }

            .kunst-title {
                font-size: 0.9rem;
                line-height: 1.2;
                margin-top: 0.35rem;
                margin-bottom: 0.22rem;
            }

            .kunst-meta-kompakt {
                font-size: 0.76rem;
                line-height: 1.25;
                margin-bottom: 0.3rem;
            }

            .stButton > button,
            .stDownloadButton > button {
                min-height: 2rem;
                font-size: 0.85rem;
                padding-top: 0.18rem;
                padding-bottom: 0.18rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )