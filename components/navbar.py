# import dash_bootstrap_components as dbc
# from flask_login import current_user
# from flask import has_request_context
# from flask_login import AnonymousUserMixin

# def navbar():
#     if has_request_context():
#         print("User:", getattr(current_user, "username", None))
#     return dbc.Navbar(
#         dbc.Container(
#             [
#                 # LEFT SIDE
#                 dbc.Nav(
#                     [
#                         dbc.NavItem(dbc.NavLink("Home", href="/")),

#                         dbc.DropdownMenu(
#                             label="Recent Studies",
#                             nav=True,
#                             in_navbar=True,
#                             children=[
#                                 dbc.DropdownMenuItem("Study 1"),
#                                 dbc.DropdownMenuItem("Study 2")
#                                 # dbc.DropdownMenuItem("Study 1", href="/study/study1"),
#                                 # dbc.DropdownMenuItem("Study 2", href="/study/study2"),
#                             ],
#                         ),

#                         dbc.DropdownMenu(
#                             label="Archive",
#                             nav=True,
#                             in_navbar=True,
#                             children=[
#                                 dbc.DropdownMenuItem("Study 3"),
#                                 dbc.DropdownMenuItem("Study 4")
#                                 # dbc.DropdownMenuItem("Study 3", href="/study/study3"),
#                                 # dbc.DropdownMenuItem("Study 4", href="/study/study4"),
#                             ],
#                         ),
#                     ],
#                     className="me-auto",
#                     navbar=True,
#                 ),

#                 dbc.Nav(
#                     auth_section(),
#                     navbar=True,
#                 ),
#             ]
#         ),
#         color="dark",
#         dark=True,
#         sticky="top",
#     )

# def auth_section():
#     if has_request_context():
        
#         if current_user.is_authenticated:
#             return [
#                 dbc.DropdownMenu(
#                     label=f"Hello {current_user.username}",
#                     nav=True,
#                     in_navbar=True,
#                     align_end=True,
#                     children=[
#                         dbc.DropdownMenuItem("User Panel", href="/admin/panel"),
#                         dbc.DropdownMenuItem(divider=True),
#                         dbc.DropdownMenuItem("Logout", href="/logout", external_link=True),
#                     ],
#                 )
#             ]
#     else:
#         print("No request context")
#     # default if no request or anonymous
#     return [dbc.NavItem(dbc.NavLink("Login", href="/login", external_link=True))]