import Foundation

/// Client for the M1 transform service (src/service/app.py is the contract).
final class RetAInClient {
    static let shared = RetAInClient()
    private let session: URLSession
    private let decoder: JSONDecoder = { let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase; return d }()

    init(session: URLSession = .shared) { self.session = session }

    var baseURL: URL { SessionStore.serverURL }

    private func request(_ path: String, method: String = "GET", body: [String: Any]? = nil, auth: Bool = true,
                         query: [URLQueryItem] = []) throws -> URLRequest {
        var url = baseURL.appending(path: path)
        if !query.isEmpty { url = url.appending(queryItems: query) }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = 60
        if auth {
            guard let token = SessionStore.token else { throw APIError.noSession }
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        return req
    }

    private func send<T: Decodable>(_ req: URLRequest, as type: T.Type) async throws -> T {
        let (data, response) = try await session.data(for: req)
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        if code >= 400 {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"]
            throw APIError.http(code, (detail as? String) ?? String(data: data, encoding: .utf8) ?? "")
        }
        do { return try decoder.decode(T.self, from: data) }
        catch { throw APIError.decode(String(describing: error)) }
    }

    // MARK: auth
    func signInWithApple(identityToken: String, nonce: String) async throws -> AuthResponse {
        try await send(request("v1/auth/apple", method: "POST",
                               body: ["identity_token": identityToken, "nonce": nonce], auth: false), as: AuthResponse.self)
    }
    func me() async throws -> Me { try await send(request("v1/me"), as: Me.self) }

    // MARK: words
    private struct WordsEnvelope: Decodable { let words: [Word] }
    func words() async throws -> [Word] { try await send(request("v1/words"), as: WordsEnvelope.self).words }
    func addWord(_ word: String, definition: String? = nil) async throws -> Word {
        var body: [String: Any] = ["word": word]
        if let definition, !definition.isEmpty { body["definition"] = definition }
        return try await send(request("v1/words", method: "POST", body: body), as: Word.self)
    }
    func setWordStatus(_ id: Int, _ status: String) async throws -> Word {
        try await send(request("v1/words/\(id)", method: "PATCH", body: ["status": status]), as: Word.self)
    }

    // MARK: transform
    func transform(text: String, title: String?, url: String?, source: String, meta: [String: Any]? = nil) async throws -> TransformAccepted {
        var body: [String: Any] = ["text": text, "title": title ?? "", "url": url ?? "", "source": source]
        if let meta { body["meta"] = meta }
        return try await send(request("v1/transform", method: "POST", body: body), as: TransformAccepted.self)
    }
    /// Phases as the server passes them, then the finished piece (or an error).
    func events(pieceId: String) throws -> AsyncThrowingStream<TransformEvent, Error> {
        var req = try request("v1/transform/\(pieceId)/events")
        req.timeoutInterval = 300
        req.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        let decoder = self.decoder
        return AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    for try await (event, data) in SSEReader.events(for: req) {
                        switch event {
                        case "phase": continuation.yield(.phase(data))
                        case "piece":
                            let piece = try decoder.decode(Piece.self, from: Data(data.utf8))
                            continuation.yield(.piece(piece))
                        case "error": continuation.yield(.error(data))
                        default: break
                        }
                    }
                    continuation.finish()
                } catch { continuation.finish(throwing: error) }
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    // MARK: diagnostics (metadata only, never content)
    func diagnostic(kind: String, payload: [String: Any]) async {
        guard let req = try? request("v1/diagnostics", method: "POST", body: ["kind": kind, "payload": payload]) else { return }
        _ = try? await session.data(for: req)
    }

    // MARK: pieces
    private struct PiecesEnvelope: Decodable { let pieces: [PieceSummary] }
    func pieces(limit: Int = 50) async throws -> [PieceSummary] {
        try await send(request("v1/pieces", query: [URLQueryItem(name: "limit", value: String(limit))]), as: PiecesEnvelope.self).pieces
    }
    func piece(_ id: String) async throws -> Piece { try await send(request("v1/pieces/\(id)"), as: Piece.self) }
    private struct OK: Decodable { let ok: Bool }
    func tap(pieceId: String, word: String) async throws {
        _ = try await send(request("v1/pieces/\(pieceId)/taps", method: "POST", body: ["word": word]), as: OK.self)
    }
}
