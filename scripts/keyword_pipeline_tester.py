#!/usr/bin/env python3
"""
키워드 추출 + DB 쿼리 테스트 도구

Dify 없이도 백엔드에서 질문 → 키워드 추출 → 쿼리 실행 순서를 검증할 수 있도록
간단한 CLI를 제공합니다.
"""
import argparse
import logging
from typing import Optional

from database import db
from process_query_builder import query_builder
from question_analyzer import question_analyzer, ProcessInfo


logger = logging.getLogger(__name__)


def _format_process_info(process_info: ProcessInfo) -> str:
    fields = [
        ("site_id", process_info.site_id),
        ("factory_id", process_info.factory_id),
        ("line_id", process_info.line_id),
        ("process_id", process_info.process_id),
        ("model_id", process_info.model_id),
        ("eqp_id", process_info.eqp_id),
        ("down_type", process_info.down_type),
        ("status_id", process_info.status_id),
        ("error_code", process_info.error_code),
        ("down_time_minutes", process_info.down_time_minutes),
        ("down_time_min", process_info.down_time_min),
        ("down_time_max", process_info.down_time_max),
        ("start_time_from", process_info.start_time_from),
        ("start_time_to", process_info.start_time_to),
    ]
    return "\n".join([f"  - {name}: {value}" for name, value in fields if value is not None])


def _ensure_db_connection() -> bool:
    try:
        return db.test_connection()
    except Exception as exc:
        logger.error("DB 연결 실패: %s", exc)
        return False


def handle_question(question: str, execute_query: bool, limit: int) -> None:
    question = question.strip()
    if not question:
        print("⚠️  빈 질문은 처리할 수 없습니다.")
        return

    print("=" * 80)
    print(f"질문: {question}")

    process_info, is_specific = question_analyzer.analyze(question)
    print(f"\n[키워드 추출] 특정 가능 여부: {is_specific}")
    print(_format_process_info(process_info) or "  - 추출된 정보 없음")

    if not is_specific:
        print("\n공정정보가 부족하여 쿼리를 생성하지 않습니다.")
        return

    query, bind_params = query_builder.build_query(process_info)
    print("\n[생성된 쿼리]")
    print(query)
    print("\n[바인드 파라미터]")
    print(bind_params)

    if not execute_query:
        print("\n--execute-query 옵션이 없어 실제 DB 실행은 생략합니다.")
        return

    if not _ensure_db_connection():
        print("\n⚠️  DB 연결에 실패했습니다. 환경 변수를 확인하세요.")
        return

    try:
        results = query_builder.execute_query(query, bind_params, limit=limit)
    except Exception as exc:
        print(f"\n❌ 쿼리 실행 중 오류가 발생했습니다: {exc}")
        return

    print(f"\n[쿼리 결과] 총 {len(results)}건 (표시 제한 {limit}건)")
    for idx, row in enumerate(results, 1):
        informnote_id = row.get("informnote_id") or row.get("INFORMNOTE_ID")
        site_id = row.get("site_id") or row.get("SITE_ID")
        factory_id = row.get("factory_id") or row.get("FACTORY_ID")
        down_time = row.get("down_time_minutes") or row.get("DOWN_TIME_MINUTES")
        print(f"  [{idx}] ID={informnote_id}, SITE={site_id}, FACTORY={factory_id}, DOWN={down_time}분")


def run_cli(question: Optional[str], execute_query: bool, limit: int) -> None:
    if question:
        handle_question(question, execute_query, limit)
        return

    print("키워드 파이프라인 테스트 CLI (종료: exit)")
    while True:
        try:
            user_input = input("\n질문 입력> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("종료합니다.")
            break

        handle_question(user_input, execute_query, limit)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="키워드 기반 쿼리 테스트 도구")
    parser.add_argument(
        "--question",
        type=str,
        help="단일 질문만 테스트할 경우 지정 (없으면 인터랙티브 모드)",
    )
    parser.add_argument(
        "--execute-query",
        action="store_true",
        help="실제 Oracle DB에 쿼리를 실행합니다.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="DB 실행 시 반환 받을 최대 행 수 (기본값 10)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="로깅 레벨 (DEBUG, INFO, WARNING, ...)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_cli(args.question, args.execute_query, args.limit)


if __name__ == "__main__":
    main()

