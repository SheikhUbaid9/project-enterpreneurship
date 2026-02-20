from pydantic import BaseModel

from shared.jsonrpc import JsonRpcRequest, JsonRpcResponse


class JsonRpcEnvelope(BaseModel):
    request: JsonRpcRequest


class JsonRpcEnvelopeResponse(BaseModel):
    response: JsonRpcResponse
