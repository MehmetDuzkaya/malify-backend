from bs4 import BeautifulSoup


class GazetteParser:
    """Ham HTML'den temiz metin çıkaran yardımcı sınıf."""

    @staticmethod
    def extract_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Script ve style etiketlerini kaldır
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Ana içerik alanını bul
        main_content = soup.find("div", class_="icerik") or soup.find("body")

        if not main_content:
            return soup.get_text(separator="\n", strip=True)

        lines = [
            line.strip()
            for line in main_content.get_text(separator="\n").splitlines()
            if line.strip()
        ]
        return "\n".join(lines)
