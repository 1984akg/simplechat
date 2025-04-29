# lambda/index.py

import json
import os
import urllib.request
import urllib.error

# FastAPI エンドポイント URL を環境変数から取得
FASTAPI_URL = os.environ.get("FASTAPI_URL")
if not FASTAPI_URL:
    raise RuntimeError("Environment variable FASTAPI_URL is required")

def lambda_handler(event, context):
    try:
        # ログ出力
        print("Received event:", json.dumps(event))

        # Cognito 認証情報があればログ出力
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event.get('body', '{}'))
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴を組み立て
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })

        # FastAPI に推論リクエストを投げる
        payload = json.dumps({
            "message": message,
            "conversationHistory": conversation_history
        }).encode("utf-8")

        req = urllib.request.Request(
            FASTAPI_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req) as res:
            res_body = json.loads(res.read().decode("utf-8"))

        # FastAPI のレスポンス構造に合わせて応答を取得
        assistant_response = res_body.get("response") or res_body.get("answer")
        if not assistant_response:
            raise Exception("No response from custom model API")

        # 会話履歴にアシスタント応答を追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスを返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
