"""
RAG CLI 도구

사용법:
    python -m src.rag.cli index <path> [--collection NAME] [--recursive]
    python -m src.rag.cli status [--collection NAME]
"""

import argparse
import sys
from pathlib import Path

from .indexer import index_document, index_directory, get_indexed_documents
from .vector_store import get_client, list_collections, DEFAULT_COLLECTION_NAME


def progress_callback(message: str, current: int, total: int):
    """진행률 출력"""
    if total > 0:
        percent = (current / total) * 100
        print(f"\r[{percent:5.1f}%] {message}", end="", flush=True)
    else:
        print(f"\r{message}", end="", flush=True)


def cmd_index(args):
    """인덱스 명령"""
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {path}")
        return 1
    
    print(f"📂 인덱싱 시작: {path}")
    print(f"   컬렉션: {args.collection}")
    
    if path.is_file():
        result = index_document(
            path,
            collection_name=args.collection,
            progress_callback=progress_callback if not args.quiet else None,
        )
        print()  # 줄바꿈
        
        if result["success"]:
            print(f"✅ 성공: {result['chunks_indexed']}개 청크 인덱싱")
            return 0
        else:
            print(f"❌ 실패: {result['error']}")
            return 1
    
    else:
        result = index_directory(
            path,
            collection_name=args.collection,
            recursive=args.recursive,
            progress_callback=progress_callback if not args.quiet else None,
        )
        print()  # 줄바꿈
        
        print(f"\n📊 결과:")
        print(f"   전체 파일: {result['total_files']}")
        print(f"   성공: {result['indexed_files']}")
        print(f"   실패: {result['failed_files']}")
        print(f"   총 청크: {result['total_chunks']}")
        
        if result["errors"]:
            print(f"\n❌ 에러:")
            for error in result["errors"][:10]:
                print(f"   - {error}")
            if len(result["errors"]) > 10:
                print(f"   ... 외 {len(result['errors']) - 10}개")
        
        return 0 if result["success"] else 1


def cmd_status(args):
    """상태 명령"""
    print("📊 RAG 인덱스 상태")
    
    try:
        client = get_client()
        collections = list_collections(client)
        
        if not collections:
            print("   컬렉션 없음")
            return 0
        
        for name in collections:
            collection = client.get_collection(name)
            count = collection.count()
            print(f"\n   📁 {name}")
            print(f"      청크 수: {count}")
            
            # 문서 목록
            docs = get_indexed_documents(name)
            print(f"      문서 수: {len(docs)}")
            if docs and len(docs) <= 10:
                for doc in sorted(docs):
                    print(f"        - {doc}")
            elif docs:
                for doc in sorted(list(docs)[:5]):
                    print(f"        - {doc}")
                print(f"        ... 외 {len(docs) - 5}개")
        
        return 0
    
    except Exception as e:
        print(f"❌ 상태 조회 실패: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="RAG 인덱싱 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="명령")
    
    # index 명령
    index_parser = subparsers.add_parser("index", help="문서 인덱싱")
    index_parser.add_argument("path", help="파일 또는 디렉토리 경로")
    index_parser.add_argument(
        "-c", "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help=f"컬렉션 이름 (기본: {DEFAULT_COLLECTION_NAME})",
    )
    index_parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="하위 디렉토리 포함",
    )
    index_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="진행률 출력 안함",
    )
    
    # status 명령
    status_parser = subparsers.add_parser("status", help="인덱스 상태 조회")
    status_parser.add_argument(
        "-c", "--collection",
        default=None,
        help="특정 컬렉션만 조회",
    )
    
    args = parser.parse_args()
    
    if args.command == "index":
        return cmd_index(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
