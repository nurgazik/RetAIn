import SwiftUI
import UIKit

extension Color {
    /// The app's primary colour (founder 2026-10-31: mint/teal). Darker in light mode so bold text on white
    /// stays readable (~3.7:1, enough for large bold text); brighter in dark mode.
    static let brand = Color(UIColor { $0.userInterfaceStyle == .dark
        ? UIColor(red: 0.18, green: 0.83, blue: 0.75, alpha: 1)     // #2DD4BF
        : UIColor(red: 0.05, green: 0.58, blue: 0.53, alpha: 1) })  // #0D9488
}
