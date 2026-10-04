import SwiftUI

struct SettingsView: View {
    @Environment(SessionState.self) private var session
    @State private var me: Me?
    @State private var serverURL = SessionStore.defaults.string(forKey: "serverURL") ?? ""
    @State private var reminder = PracticeReminder.isOn

    var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    if let me {
                        LabeledContent("User", value: me.email ?? me.userId)
                        LabeledContent("Learning words", value: "\(me.learningWords)")
                        LabeledContent("Reads", value: "\(me.pieces)")
                        LabeledContent("Spend today", value: String(format: "$%.3f", me.spendTodayUsd ?? 0))
                        LabeledContent("Spend this month", value: String(format: "$%.2f", me.spendMonthUsd ?? 0))
                    }
                    Button("Sign out", role: .destructive) { SessionStore.token = nil; session.signedIn = false }
                }
                Section("Practice") {
                    Toggle("Daily reminder at 7 pm", isOn: $reminder)
                        .onChange(of: reminder) { _, on in
                            if on { Task { reminder = await PracticeReminder.enable() } } else { PracticeReminder.disable() }
                        }
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
