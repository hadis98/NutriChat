from html import escape


SVG_ICONS = {
    "chat": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5.75A3.75 3.75 0 0 1 8.75 2h6.5A3.75 3.75 0 0 1 19 5.75v4.5A3.75 3.75 0 0 1 15.25 14H10l-4.2 3.15A.5.5 0 0 1 5 16.75V14.2A3.75 3.75 0 0 1 2 10.55v-4.8Z"/><path d="M8 7h8M8 10h5"/></svg>
    """,
    "lightbulb": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4"/><path d="M8.2 14.2A6.5 6.5 0 1 1 15.8 14c-.8.65-1.3 1.45-1.45 2.4h-4.7c-.15-.87-.65-1.6-1.45-2.2Z"/><path d="M12 2v2M4.9 4.9l1.4 1.4M19.1 4.9l-1.4 1.4M2 12h2M20 12h2"/></svg>
    """,
    "shield": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 19 5.4v5.7c0 4.4-2.7 8.4-7 10.1-4.3-1.7-7-5.7-7-10.1V5.4l7-2.6Z"/><path d="m9 12 2 2 4-4"/></svg>
    """,
    "shield_diamond": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 19 5.4v5.7c0 4.4-2.7 8.4-7 10.1-4.3-1.7-7-5.7-7-10.1V5.4l7-2.6Z"/><path d="M12 8.2 15.8 12 12 15.8 8.2 12 12 8.2Z"/></svg>
    """,
    "book": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z"/><path d="M4 5.5v15A2.5 2.5 0 0 1 6.5 18H20M8 7h8M8 10h6"/></svg>
    """,
    "layers": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 8 4.2-8 4.2-8-4.2L12 3Z"/><path d="m4 12 8 4.2 8-4.2M4 16.7l8 4.3 8-4.3"/></svg>
    """,
    "server": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="6" rx="1.8"/><rect x="4" y="14" width="16" height="6" rx="1.8"/><path d="M8 7h.01M8 17h.01M12 7h4M12 17h4"/></svg>
    """,
    "expand_arrows": """
      <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 4h6v6" />
      <path d="M20 4l-7 7" />
      <path d="M10 20H4v-6" />
      <path d="M4 20l7-7" />
      </svg>
    """,
    "clock": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>
    """,
    "zap": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2.8 4.5 13h6.7L10.8 21.2 19.5 10h-6.7L13 2.8Z"/></svg>
    """,
    "stopwatch": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="13" r="7.5"/><path d="M9.5 2.8h5M12 6V3M12 9.5V13l2.2 1.7M18.2 6.8l1.2-1.2"/></svg>
    """,
    "activity": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 12h4l2.2-5.5 4.6 11 2.1-5.5h4.1"/></svg>
    """,
    "bar_chart": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 16V9"/><path d="M12 16V6"/><path d="M16 16v-4"/></svg>
    """,
    "flask": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6"/><path d="M10 3v5.4L5.5 18A2 2 0 0 0 7.3 21h9.4a2 2 0 0 0 1.8-3L14 8.4V3"/><path d="M7.8 16h8.4"/></svg>
    """,
    "file_text": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l4 4v14H7V3Z"/><path d="M14 3v5h5"/><path d="M9.5 12h5"/><path d="M9.5 15h5"/><path d="M9.5 18h3"/></svg>
    """,
    "copy": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h2"/></svg>
    """,
    "github": """
      <svg class="nc-github-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8a9.3 9.3 0 0 0-2.94 18.12c.47.09.64-.2.64-.45v-1.8c-2.63.57-3.18-1.12-3.18-1.12-.43-1.09-1.05-1.38-1.05-1.38-.86-.59.07-.58.07-.58.95.07 1.45.98 1.45.98.85 1.45 2.22 1.03 2.76.79.09-.61.33-1.03.6-1.27-2.1-.24-4.31-1.05-4.31-4.68 0-1.03.37-1.88.98-2.54-.1-.24-.43-1.2.09-2.5 0 0 .8-.26 2.56.97A8.9 8.9 0 0 1 12 7.03a8.9 8.9 0 0 1 2.33.31c1.77-1.23 2.56-.97 2.56-.97.52 1.3.19 2.26.09 2.5.61.66.98 1.51.98 2.54 0 3.64-2.21 4.44-4.32 4.68.34.29.64.87.64 1.76v2.62c0 .25.17.54.65.45A9.3 9.3 0 0 0 12 2.8Z"/></svg>
    """,
    "trend_up": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17h16"/><path d="m6 14 4-4 3 3 5-7"/><path d="M16 6h2v2"/></svg>
    """,
    "target": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/></svg>
    """,
    "chart_line": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 4-4 3 2 4-6"/></svg>
    """,
    "alert_circle": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5"/><path d="M12 16.5h.01"/></svg>
    """,
    "calculator": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8"/><path d="M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01"/></svg>
    """,
    "search": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>
    """,
    "sprout": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20V9"/><path d="M12 10C7.6 10 5.2 7.2 5 4c4.2.1 7 2.1 7 6Z"/><path d="M12 13c3.7 0 6.3-2.2 6.8-5.8-4.4.2-6.8 2.4-6.8 5.8Z"/><path d="M8 20h8"/></svg>
    """,
    "droplet": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8s6.5 7.1 6.5 12.1A6.5 6.5 0 0 1 5.5 14.9C5.5 9.9 12 2.8 12 2.8Z"/></svg>
    """,
    "wheat": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22V3"/><path d="M12 7c-3.2 0-5.2-1.5-6-4 3.4 0 5.4 1.4 6 4ZM12 12c-3.2 0-5.2-1.5-6-4 3.4 0 5.4 1.4 6 4ZM12 17c-3.2 0-5.2-1.5-6-4 3.4 0 5.4 1.4 6 4ZM12 7c3.2 0 5.2-1.5 6-4-3.4 0-5.4 1.4-6 4ZM12 12c3.2 0 5.2-1.5 6-4-3.4 0-5.4 1.4-6 4ZM12 17c3.2 0 5.2-1.5 6-4-3.4 0-5.4 1.4-6 4Z"/></svg>
    """,
    "bone": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.2 8.7a3 3 0 1 1 3-3 3 3 0 1 1 3.1 3.1l-4.5 4.5a3 3 0 1 1-3.1 3.1 3 3 0 1 1-3-3l4.5-4.7Z"/></svg>
    """,
    "cube": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2.8 8 4.6v9.2l-8 4.6-8-4.6V7.4l8-4.6Z"/><path d="m4 7.4 8 4.6 8-4.6M12 12v9.2"/></svg>
    """,
    "blocks": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/><path d="M7 8V6.5a1 1 0 0 1 2 0V8M6.4 8h3.2M15.5 6h2a1.5 1.5 0 0 1 0 3h-2V6ZM15.5 9H18a1.5 1.5 0 0 1 0 3h-2.5V9ZM8.8 15.8A2.5 2.5 0 1 0 9 18.2"/></svg>
    """,
    "user": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4.2 4.2 0 1 0 0-8.4 4.2 4.2 0 0 0 0 8.4Z"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/></svg>
    """,
    "stethoscope": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4v5a4 4 0 0 0 8 0V4"/><path d="M4 4h4M12 4h4M10 13v2.5a4.5 4.5 0 0 0 9 0V14"/><circle cx="19" cy="12" r="2"/></svg>
    """,
    "gear": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.4 1.1V21a2 2 0 0 1-4 0v-.1A1.65 1.65 0 0 0 8.6 19a1.65 1.65 0 0 0-1.82-.33l-.08.04a2 2 0 1 1-2-3.46l.08-.04A1.65 1.65 0 0 0 5.6 13a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1.1-.4H3.8a2 2 0 0 1 0-4h.1A1.65 1.65 0 0 0 5.8 6.6a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 10 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .4-1.1V3a2 2 0 0 1 4 0v.1A1.65 1.65 0 0 0 16.4 5a1.65 1.65 0 0 0 1.82.33l.08-.04a2 2 0 1 1 2 3.46l-.08.04A1.65 1.65 0 0 0 19.4 11c0 .4.14.78.4 1.1.28.32.66.5 1.1.5h.1a2 2 0 0 1 0 4h-.1a1.65 1.65 0 0 0-1.5-1.6Z"/></svg>
    """,
    "refresh": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>
    """,
    "info": """
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
    """,
     "vitamin_softgel": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8.5 15.5 15.5 8.5" />
      <path d="M7.6 16.4a4.2 4.2 0 0 1 0-5.9l2.9-2.9a4.2 4.2 0 0 1 5.9 5.9l-2.9 2.9a4.2 4.2 0 0 1-5.9 0Z" />
      <path d="M16.2 15.4c2.1-.5 3.8.4 4.8 2.4-2.3.8-4.1.2-5.1-1.7" />
      <path d="M16.1 16.1c.9 1.7.4 3.3-1.3 4.6-1.1-2-.8-3.6.9-4.8" />
    </svg>
    """,

    "mouth_sparkle": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12c2.4-2.7 4.3-3.2 7-1.2 2.7-2 4.6-1.5 7 1.2" />
      <path d="M5.5 12.5c3.8 3.3 9.2 3.3 13 0" />
      <path d="M17.7 6.3l.5 1.1 1.1.5-1.1.5-.5 1.1-.5-1.1-1.1-.5 1.1-.5.5-1.1Z" />
      <path d="M19.2 15.2l.4.8.8.4-.8.4-.4.8-.4-.8-.8-.4.8-.4.4-.8Z" />
    </svg>
    """,

    "fiber_wheat": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 4v16" />
      <path d="M12 7c-2.3-.3-3.7-1.3-4.4-3 2.3.1 3.8 1.1 4.4 3Z" />
      <path d="M12 10c2.3-.3 3.7-1.3 4.4-3-2.3.1-3.8 1.1-4.4 3Z" />
      <path d="M12 13c-2.3-.3-3.7-1.3-4.4-3 2.3.1 3.8 1.1 4.4 3Z" />
      <path d="M12 16c2.3-.3 3.7-1.3 4.4-3-2.3.1-3.8 1.1-4.4 3Z" />
    </svg>
    """,

    "bone_sparkle": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7.5 14.5 14.5 7.5" />
      <path d="M6.2 17.8a2.5 2.5 0 1 1-2-4 2.5 2.5 0 1 1 3.6-3.6l6-6a2.5 2.5 0 1 1 3.6 3.6 2.5 2.5 0 1 1-3.6 3.6l-6 6a2.5 2.5 0 0 1-1.6.4Z" />
      <path d="M17.5 15.5l.5 1.1 1.1.5-1.1.5-.5 1.1-.5-1.1-1.1-.5 1.1-.5.5-1.1Z" />
    </svg>
    """,

    "water_glass": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 4h10l-1.2 16H8.2L7 4Z" />
      <path d="M8 9h8" />
      <path d="M12 12.2c1.4 1.5 2.1 2.5 2.1 3.5a2.1 2.1 0 0 1-4.2 0c0-1 .7-2 2.1-3.5Z" />
    </svg>
    """,

    "macro_plate": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 4v16" />
      <path d="M4 12h16" />
      <path d="M8.5 8.5c1.4-1 2.6-1.2 3.5-.5" />
      <path d="M15.5 15.5c-1.4 1-2.6 1.2-3.5.5" />
      <path d="M15.7 8.2h.1" />
      <path d="M8.2 15.8h.1" />
    </svg>
    """,

    "assessment_clipboard": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M9 4h6l1 2h2v15H6V6h2l1-2Z" />
      <path d="M9 4h6" />
      <path d="M9 10h6" />
      <path d="M9 14h5" />
      <path d="M9 18h3" />
      <path d="M16 17.5l1.2 1.2 2.4-2.8" />
    </svg>
    """,

    "egg_protein": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 4c3.3 0 6 4.2 6 8.7 0 4.2-2.4 7.3-6 7.3s-6-3.1-6-7.3C6 8.2 8.7 4 12 4Z" />
      <path d="M14.5 16.2c-1 .7-2.3.9-3.6.5" />
    </svg>
    """,

    "immune_shield": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.5 19 6v5.5c0 4.3-2.7 7.4-7 9-4.3-1.6-7-4.7-7-9V6l7-2.5Z" />
      <path d="M12 8v6" />
      <path d="M9 11h6" />
      <path d="M18.5 4.5l.4.9.9.4-.9.4-.4.9-.4-.9-.9-.4.9-.4.4-.9Z" />
    </svg>
    """,

    "sugar_fruit": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 8.5 8 6l4 2.5v5L8 16l-4-2.5v-5Z" />
      <path d="M8 6v5l4 2.5" />
      <path d="M8 11 4 8.5" />
      <path d="M16.8 9.5c2.2 0 3.7 1.7 3.7 4.4 0 3-1.8 5.2-3.8 5.2-.8 0-1.2-.3-1.7-.3s-.9.3-1.7.3c-1.8 0-3.3-1.8-3.6-4.2" />
      <path d="M16 7.8c.7-1.3 1.8-1.7 3.2-1.5-.4 1.3-1.4 2-3.2 1.5Z" />
    </svg>
    """,

    "credential_people": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="8" cy="8" r="2.5" />
      <circle cx="16" cy="8" r="2.5" />
      <path d="M4 18c.5-2.7 2-4 4-4 1.2 0 2.2.5 3 1.4" />
      <path d="M13 14.5c.7-.4 1.7-.5 3-.5 2 0 3.5 1.3 4 4" />
      <path d="M12 14.5l2 1 2-1v3.1c0 1.2-.8 2.2-2 2.8-1.2-.6-2-1.6-2-2.8v-3.1Z" />
    </svg>
    """,

    "carbs_compare": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 18 19 6" />
      <path d="M5.5 8.5 8 6l2.5 2.5L8 11 5.5 8.5Z" />
      <path d="M14 16c0-2 1.4-3.5 3-3.5s3 1.5 3 3.5v2h-6v-2Z" />
      <path d="M14 18h6" />
    </svg>
    """,

    "alcohol_beverages": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 4h3v4l1 2v10H5V10l1-2V4Z" />
      <path d="M5 13h5" />
      <path d="M14 6h5c0 3-1 5-2.5 5S14 9 14 6Z" />
      <path d="M16.5 11v5" />
      <path d="M14.5 16h4" />
      <path d="M19 13h2v7h-2v-7Z" />
    </svg>
    """,

    "liver_warning": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 14c0-4 2.8-7 7-7h2c3 0 5 1.8 5 4.3 0 2.3-1.5 3.7-4 3.7h-3c-2 0-3.5 1-4.5 3H5v-4Z" />
      <path d="M17.5 15.5 21 21h-7l3.5-5.5Z" />
      <path d="M17.5 17.5v1.2" />
      <path d="M17.5 20h.1" />
    </svg>
    """,

    "electrolyte_drop": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3c4 4.5 6 7.8 6 10.6A6 6 0 0 1 6 13.6C6 10.8 8 7.5 12 3Z" />
      <path d="M13 8.5 10.5 13H13l-2 4.5 4-5h-2.5L13 8.5Z" />
    </svg>
    """,

    "mineral_warning": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 15.5 15.5 8" />
      <path d="M7.5 16.5a4 4 0 0 1 0-5.7l3.3-3.3a4 4 0 1 1 5.7 5.7l-3.3 3.3a4 4 0 0 1-5.7 0Z" />
      <path d="M17.5 15.5 21 21h-7l3.5-5.5Z" />
      <path d="M17.5 17.5v1.2" />
      <path d="M17.5 20h.1" />
    </svg>
    """,

    "baby_bottle": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 4h4v3h-4V4Z" />
      <path d="M9 7h6l1 2v10a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V9l1-2Z" />
      <path d="M9 12h6" />
      <path d="M12 14c1.1 1.1 1.6 1.9 1.6 2.6a1.6 1.6 0 0 1-3.2 0c0-.7.5-1.5 1.6-2.6Z" />
    </svg>
    """,

    "prompt_lock": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      <path d="M6 10h12v9H6v-9Z" />
      <path d="M17 14.5l2 1 2-1v2.8c0 1.1-.8 2-2 2.7-1.2-.7-2-1.6-2-2.7v-2.8Z" />
    </svg>
    """,

    "business_question": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 8V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M4 8h16v11H4V8Z" />
      <path d="M9.5 12a2.5 2.5 0 0 1 5 0c0 1.7-2.5 1.8-2.5 3.3" />
      <path d="M12 18h.1" />
    </svg>
    """,

    "iron_capsule": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8.5 15.5 15.5 8.5" />
      <path d="M7.6 16.4a4.2 4.2 0 0 1 0-5.9l2.9-2.9a4.2 4.2 0 0 1 5.9 5.9l-2.9 2.9a4.2 4.2 0 0 1-5.9 0Z" />
      <path d="M6 5c1.8 2 2.7 3.5 2.7 4.7a2.7 2.7 0 0 1-5.4 0C3.3 8.5 4.2 7 6 5Z" />
    </svg>
    """,

    "glucose_meter": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="6" y="4" width="8" height="13" rx="2" />
      <path d="M8.5 7h3" />
      <path d="M9 13h2" />
      <path d="M16 14c1.4 1.5 2.1 2.5 2.1 3.4a2.1 2.1 0 0 1-4.2 0c0-.9.7-1.9 2.1-3.4Z" />
      <path d="M14 20h5" />
    </svg>
    """,

    "personal_diet": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="12" r="5" />
      <path d="M4 5v14" />
      <path d="M19 5v14" />
      <path d="M17 5v5" />
      <path d="M21 5v5" />
      <path d="M17 10h4" />
      <circle cx="17.5" cy="17.5" r="2" />
      <path d="M14.5 21c.6-1.3 1.6-2 3-2s2.4.7 3 2" />
    </svg>
    """,

    "sun_capsule": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="8" cy="8" r="3" />
      <path d="M8 2v2" />
      <path d="M8 12v2" />
      <path d="M2 8h2" />
      <path d="M12 8h2" />
      <path d="M3.8 3.8l1.4 1.4" />
      <path d="M10.8 10.8l1.4 1.4" />
      <path d="M12.5 18.5 18.5 12.5" />
      <path d="M12 19a3.5 3.5 0 0 1 0-5l2-2a3.5 3.5 0 0 1 5 5l-2 2a3.5 3.5 0 0 1-5 0Z" />
    </svg>
    """,

    "blood_medical": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 3c3.5 4 5.2 6.8 5.2 9.2a5.2 5.2 0 0 1-10.4 0C4.8 9.8 6.5 7 10 3Z" />
      <path d="M17 13v6" />
      <path d="M14 16h6" />
    </svg>
    """,

    "medicine_scale": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 5h6v4H7V5Z" />
      <path d="M6 9h8v11H6V9Z" />
      <path d="M9 14h2" />
      <path d="M10 13v2" />
      <path d="M16 13h5v6h-5v-6Z" />
      <path d="M18.5 15.5h.1" />
      <path d="M17 18h3" />
    </svg>
    """,

    "book_scope": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 5.5c2.8-.8 5-.5 8 1.1v13c-3-1.6-5.2-1.9-8-1.1v-13Z" />
      <path d="M20 5.5c-2.8-.8-5-.5-8 1.1v13c3-1.6 5.2-1.9 8-1.1v-13Z" />
      <path d="M15.5 10a2 2 0 1 1 3.3 1.5c-.8.7-1.3 1.1-1.3 2" />
      <path d="M17.5 16h.1" />
      <path d="M20 4l1.5-1.5" />
      <path d="M20 4h2" />
      <path d="M20 4v-2" />
    </svg>
    """,

    "fallback": """
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
      <path d="M9.5 9a2.7 2.7 0 0 1 5.2 1c0 1.9-2.7 2-2.7 3.8" />
      <path d="M12 17h.1" />
    </svg>
    """,
}


def svg_icon(name: str, extra_class: str = "") -> str:
    class_attr = f' class="{escape(extra_class)}"' if extra_class else ""
    return f'<span{class_attr}>{SVG_ICONS.get(name, SVG_ICONS["fallback"])}</span>'
