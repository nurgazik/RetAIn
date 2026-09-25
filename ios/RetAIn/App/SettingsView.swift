import SwiftUI

struct SettingsView: View {
    @Environment(SessionState.self) private var session
    @State private var me: Me?
    @State private var serverURL = SessionStore.defaults.string(forKey: "serverURL") ?? ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    if let me { LabeledContent("User", value: me.email ?? me.userId); LabeledContent("Learning words", value: "\(me.learningWords)"); LabeledContent("Reads", value: "\(me.pieces)") }
                    Button("Sign out", role: .destructive) { SessionStore.token = nil; session.signedIn = false }
                }
                Section("Server") {
                    LabeledContent("Default", value: (Bundle.main.object(forInfoDictionaryKey: "RETAIN_SERVER") as? String) ?? "")
                    TextField("Override URL (blank = default)", text: $serverURL).textInputAutocapitalization(.never).autocorrectionDisabled()
                        .onSubmit { SessionStore.setServerURL(serverURL) }
                }
                Section { Text("Adapted with AI to carry your words: phrasing may be added or changed, facts should not be — check the original for anything that matters.").font(.footnote).foregroundStyle(.secondary) }
            }
            .navigationTitle("Settings")
            .task { me = try? await RetAInClient.shared.me() }
        }
    }
}
