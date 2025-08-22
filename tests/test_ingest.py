import pytest
import pandas as pd
from unittest.mock import patch, mock_open
from src.ingest import process_ticket_group, chunk_document, process_tickets_in_chunks, process_knowledge_files

# Test for process_ticket_group
def test_process_ticket_group():
    # Sample data for a ticket group
    data = {
        'ticket_id': [123, 123],
        'subject': ['Order Issue', 'Order Issue'],
        'channel': ['email', 'email'],
        'status': ['closed', 'closed'],
        'sender': ['customer', 'agent'],
        'body': ['My order is late.', 'We are looking into it.'],
        'sent_datetime': ['2023-01-01 10:00:00', '2023-01-01 10:05:00']
    }
    df = pd.DataFrame(data)

    result = process_ticket_group(df)

    assert result['id'] == 'ticket_123'
    assert 'My order is late.' in result['text']
    assert 'We are looking into it.' in result['text']
    assert result['metadata']['ticket_id'] == 123
    assert result['metadata']['subject'] == 'Order Issue'

# Test for chunk_document
def test_chunk_document():
    doc = {
        "id": "test_doc",
        "text": "This is a long document that needs to be chunked. It has multiple sentences and should be split into smaller pieces.",
        "metadata": {"source": "test"}
    }
    
    # Mock CHUNK_SIZE_CHARS and CHUNK_OVERLAP for consistent testing
    with patch('src.ingest.CHUNK_SIZE_CHARS', 20):
        with patch('src.ingest.CHUNK_OVERLAP', 5):
            chunks = list(chunk_document(doc))

            assert len(chunks) > 1
            assert chunks[0]['id'] == 'test_doc_chunk_0'
            assert chunks[0]['metadata'] == {"source": "test"}
            assert len(chunks[0]['text']) <= 20
            assert chunks[1]['id'] == 'test_doc_chunk_1'

# Test for process_tickets_in_chunks (mocking file read)
@patch('pandas.read_csv')
def test_process_tickets_in_chunks(mock_read_csv):
    # Mock the behavior of pd.read_csv to return chunks of data
    mock_read_csv.return_value = iter([
        pd.DataFrame({
            'ticket_id': [1, 2],
            'subject': ['Sub1', 'Sub2'],
            'channel': ['email', 'phone'],
            'status': ['closed', 'open'],
            'sender': ['cust', 'cust'],
            'body': ['Body1', 'Body2'],
            'sent_datetime': ['2023-01-01', '2023-01-02']
        }),
        pd.DataFrame({
            'ticket_id': [3, 4],
            'subject': ['Sub3', 'Sub4'],
            'channel': ['chat', 'email'],
            'status': ['closed', 'closed'],
            'sender': ['cust', 'cust'],
            'body': ['Body3', 'Body4'],
            'sent_datetime': ['2023-01-03', '2023-01-04']
        })
    ])

    tickets = list(process_tickets_in_chunks())
    assert len(tickets) == 3  # Expect 3 closed tickets in the mock data
    assert tickets[0]['id'] == 'ticket_1'
    assert tickets[1]['id'] == 'ticket_3'

# Test for process_knowledge_files (mocking file system operations)
@patch('glob.glob') # Patch glob.glob
@patch('builtins.open', new_callable=mock_open, read_data='file content')
def test_process_knowledge_files(mock_open, mock_glob):
    def mock_glob_side_effect(path, recursive=False):
        if '*.txt' in path:
            return ['/fake/path/faq.md']
        elif '*.md' in path:
            return ['/fake/path/policy.txt']
        return []

    mock_glob.side_effect = mock_glob_side_effect

    # Mock the KNOWLEDGE_PATH to avoid actual file system access
    with patch('src.ingest.KNOWLEDGE_PATH', '/fake/path/'):
        knowledge_docs = list(process_knowledge_files())

        assert len(knowledge_docs) == 2
        assert knowledge_docs[0]['id'] == 'knowledge_faq.md'
        assert knowledge_docs[0]['text'] == 'file content'
        assert knowledge_docs[1]['id'] == 'knowledge_policy.txt'
