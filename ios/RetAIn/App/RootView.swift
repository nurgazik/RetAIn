import SwiftUI
import WidgetKit

struct RootView: View {
    @Environment(SessionState.self) private var session
    @Environment(\.scenePhase) private var scenePhase
    @State private var tab = "practice"   // D64: no paste tab; reading happens from the other app's share sheet
    @State private var openWordId: Int?
    var body: some View {
        if session.signedIn {
            TabView(selection: $tab) {
                PracticeView().tabItem { Label("Practice", systemImage: "pencil.and.list.clipboard") }.tag("practice")
                WordsView(openWordId: $openWordId).tabItem { Label("Words", systemImage: "character.book.closed") }.tag("words")
                ReadsView().tabItem { Label("My Reads", systemImage: "books.vertical") }.tag("reads")
                SettingsView().tabItem { Label("Settings", systemImage: "gearshape") }.tag("settings")
            }
            .fontDesign(.rounded)   // D70: SF Pro Rounded app-wide; the reader's serif and the handwriting set their own
            .tint(.brandText)
            // The widget links to retain://word/<id>: open that word in the Words tab.
            .onOpenURL { url in
                guard let id = WordLink.id(from: url) else { return }
                tab = "words"; openWordId = id
            }
            // Keep the widget's word copy fresh even if the Words tab is never opened.
            .onChange(of: scenePhase, initial: true) { _, phase in if phase == .active { Task { await cacheWords() } } }
        } else {
            SignInView()
        }
    }

    private func cacheWords() async {
        guard let words = try? await RetAInClient.shared.words() else { return }
        WordsStore.replaceAll(words); WidgetCenter.shared.reloadAllTimelines()
    }
}

