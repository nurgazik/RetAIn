import SwiftUI

@main
struct RetAInApp: App {
    @State private var session = SessionState()
    var body: some Scene {
        WindowGroup {
            RootView().environment(session)
                .onAppear {
                    // Scripted simulator runs: `-devToken <token>` signs in as the service's dev user.
                    if let i = CommandLine.arguments.firstIndex(of: "-devToken"), i + 1 < CommandLine.arguments.count {
                        SessionStore.token = CommandLine.arguments[i + 1]
                        session.signedIn = true
                    }
                }
        }
    }
}

@Observable final class SessionState {
    var signedIn: Bool = SessionStore.isSignedIn
}
