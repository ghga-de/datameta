    """Test user management for the API
        +: Changes that should work
        -: Changes that should not work
    """

    """Test 1: Namechange
    a) Normal user:
        + change name yourself
        - change somebody else
    b) Group Admin:
        + change somebody in group
        - change somebody in other group
    c) Site Admin:
        + change somebody not in group 
    """

    """Test 2: Group Change
    a) Normal user:
        - change your group
    b) Group Admin:
        - change your group
        - change group from somebody in your group
        - change group from somebody not in your group to your group
    c) Site Admin:
        + change your own group
        + change somebody elses group
    """

    """Test 3: Admin settings change
    a) Normal user:
        - try to make yourself group/site admin
        - try to take away somebody elses admin permissions
    b) Group Admin:
        + Make user in your group Admin
        + Demote this user back
        - make yourself site admin
        - make another user site admin
        - demote a site admin
        - demote a site admin from beeing group admin in your group
    c) Site Admin:
        + Promote user to group & site admin
        + Demote user back
    """

    """Test 4: Enabled settings change:
    Note, that the enabled setting currently does not do anything. Once this changes, these tests have to be expanded
    a) Normal user:
        - disable/enabled yourself
    b) Group Admin:
        + disable/enable user in your group
        - disable/enable user in your group which is site admin
        - disable/enable user in another group
    c) Site Admin:
        + disable/enable user
    """
