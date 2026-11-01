import SwiftUI
import UIKit

/// App-only part of the notebook look (D70): the native navigation bar's titles.
enum Theme {
    /// Large titles in handwriting, inline titles in SF Pro Rounded, both ink blue; the bar itself stays native.
    static func applyNavigationBar() {
        let hand = UIFontDescriptor(fontAttributes: [.family: "Caveat"]).withSymbolicTraits(.traitBold)
            ?? UIFontDescriptor(fontAttributes: [.family: "Caveat"])
        let rounded = UIFont.systemFont(ofSize: 17, weight: .bold).fontDescriptor.withDesign(.rounded)
        let ink = UIColor(Color.brandText)
        let bar = UINavigationBar.appearance()
        bar.largeTitleTextAttributes = [.font: UIFont(descriptor: hand, size: 44), .foregroundColor: ink]
        if let rounded { bar.titleTextAttributes = [.font: UIFont(descriptor: rounded, size: 17), .foregroundColor: ink] }
    }
}
