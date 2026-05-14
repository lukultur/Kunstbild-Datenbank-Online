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
            max-width: 1180px;
            padding-top: 3rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        section[data-testid="stSidebar"] {
            background-color: #262730;
        }

        h1 {
            font-size: 2.4rem;
            letter-spacing: -0.03em;
        }

        h2, h3, h4, h5, h6,
        p, label, span, div {
            color: #f5f5f5;
        }

        .fixed-image-box {
            width: 100%;
            height: 210px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #141820;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.7rem;
        }

        .fixed-image-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .kunst-title {
            height: 2.8em;
            overflow: hidden;
            font-size: 1.02rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 0.5rem;
            margin-bottom: 0.35rem;
            color: #ffffff;
        }

        .kunst-meta {
            min-height: 4.7em;
            font-size: 0.86rem;
            line-height: 1.4;
            color: #e6e6e6;
        }
	.kunst-meta-kompakt {
            min-height: 2.6em;
            font-size: 0.86rem;
            line-height: 1.35;
            color: #d1d5db;
            margin-bottom: 0.65rem;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            padding-top: 0.45rem;
            padding-bottom: 0.45rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 14px;
            padding: 0.75rem;
        }

        div[data-testid="column"] {
            padding-left: 0.45rem;
            padding-right: 0.45rem;
        }

        input, textarea, select {
            border-radius: 8px !important;
        }

        @media (max-width: 900px) {

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 2rem;
            }

            h1 {
                font-size: 1.9rem;
            }

            .fixed-image-box {
                height: 210px;
            }

            .kunst-title {
                font-size: 0.98rem;
                height: auto;
            }

            .kunst-meta {
                font-size: 0.82rem;
                min-height: auto;
            }

        }

        @media (max-width: 640px) {

            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
                padding-top: 1.25rem;
            }

            h1 {
                font-size: 1.65rem;
                line-height: 1.15;
            }

            .fixed-image-box {
                height: 260px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding: 0.7rem;
                margin-bottom: 1rem;
            }

            .stButton > button,
            .stDownloadButton > button {
                font-size: 0.9rem;
                padding-top: 0.5rem;
                padding-bottom: 0.5rem;
            }

            .kunst-title {
                font-size: 1rem;
                margin-top: 0.55rem;
            }

            .kunst-meta {
                font-size: 0.84rem;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )