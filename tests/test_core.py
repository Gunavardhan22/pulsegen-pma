import pytest
from app.parser import DocParser
from app.module_inference import ModuleInference, ModuleInference

def test_doc_parser_cleaning():
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Menu</nav>
            <div class="sidebar">Sidebar</div>
            <main>
                <h1>Main Title</h1>
                <p>Some content.</p>
                <footer>Footer</footer>
            </main>
        </body>
    </html>
    """
    parser = DocParser(html)
    content = parser.extract_content()
    
    # Nav and Footer should be gone
    assert "Menu" not in parser.get_raw_text()
    assert "Footer" not in parser.get_raw_text()
    assert "Sidebar" not in parser.get_raw_text()
    
    # Main content should be present
    assert len(content) >= 1
    assert content[0]["heading"] == "Main Title"
    assert "Some content" in content[0]["text"]

def test_module_inference():
    urls = ["https://example.com/docs/intro"]
    inference = ModuleInference(urls)
    
    crawled_data = [
        {"url": "https://example.com/docs/intro", "title": "Intro", "content": []},
        {"url": "https://example.com/docs/api/users", "title": "Users API", "content": []}
    ]
    
    structure = inference.infer_structure(crawled_data)
    
    # "intro" should be a top level module
    assert "Intro" in structure
    
    # "api" should be top level, with "users" as submodule
    assert "Api" in structure
    assert "Users" in structure["Api"]["submodules"]
