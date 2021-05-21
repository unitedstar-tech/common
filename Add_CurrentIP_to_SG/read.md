# 使い方
- API GatewayからLambda実行して使用することを想定
- API Gatewayは"HTTP API"を使用し、"統合"のParameter mappingで"すべての受信リクエスト"に"変更するパラメータ"を**querystring.sourceIp**, "変更タイプ"を**追加**, "値"を **$context.identity.sourceIp**に設定する。
