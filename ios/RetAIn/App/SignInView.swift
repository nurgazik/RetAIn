import AuthenticationServices
import CryptoKit
import SwiftUI

/// Sign in with Apple → POST /v1/auth/apple → session token in the shared keychain.
/// The nonce we hand Apple is the SHA-256 of a random string; Apple echoes that hash in
/// the identity token, so the server compares against the same hash.
struct SignInView: View {
    @Environment(SessionState.self) private var session
    @State private var nonce = SignInView.randomNonce()
    @State private var error: String?
    @State private var devToken = ""

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            Text("RetAIn").font(.system(size: 34, weight: .bold)).tracking(4)
            Text("Your words, in whatever you're reading.").foregroundStyle(.secondary)
            Spacer()
            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.email]
                request.nonce = SignInView.sha256(nonce)
            } onCompletion: { result in
                Task { await handle(result) }
            }
            .signInWithAppleButtonStyle(.black).frame(height: 50).padding(.horizontal, 32)
            if let error { Text(error).font(.caption).foregroundStyle(.red).multilineTextAlignment(.center).padding(.horizontal) }
            #if DEBUG
            VStack(spacing: 6) {
                TextField("Developer token (simulator)", text: $devToken).textFieldStyle(.roundedBorder)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                Button("Use developer token") { SessionStore.token = devToken; session.signedIn = true }
                    .disabled(devToken.isEmpty)
            }.padding(.horizontal, 32).font(.footnote)
            #endif
            Spacer(minLength: 40)
        }
    }

    private func handle(_ result: Result<ASAuthorization, Error>) async {
        switch result {
        case .failure(let e): error = e.localizedDescription
        case .success(let auth):
            guard let cred = auth.credential as? ASAuthorizationAppleIDCredential,
                  let data = cred.identityToken, let token = String(data: data, encoding: .utf8) else {
                error = "Apple returned no identity token"; return
            }
            do {
                let r = try await RetAInClient.shared.signInWithApple(identityToken: token, nonce: SignInView.sha256(nonce))
                SessionStore.token = r.token
                session.signedIn = true
            } catch { self.error = error.localizedDescription; nonce = SignInView.randomNonce() }
        }
    }

    static func randomNonce(length: Int = 32) -> String {
        let chars = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
        return String((0..<length).map { _ in chars[Int.random(in: 0..<chars.count)] })
    }
    static func sha256(_ s: String) -> String {
        SHA256.hash(data: Data(s.utf8)).map { String(format: "%02x", $0) }.joined()
    }
}
