from models import JoinedGroupMemberInfo, Accounts


def parse_ranges(input_str: str, min_range: int, max_range: int):
    # Split the input string by commas
    parts = input_str.split(',')
    result = set()

    # Process each part
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start = int(start) if start else min_range
            end = int(end) if end else max_range

            if start is not None and end is not None:
                result.update([*range(start, end)])
            elif start is not None:
                result.add(start)
        else:
            if part:
                result.add(int(part))

    # Convert the set to a sorted list
    return sorted(result)


def J_G_M_to_saveable(member: JoinedGroupMemberInfo):
    return {
        k: v for k, v in member.items() if (
                v is not None and
                k in Accounts._meta.fields_map.keys()
        )
    }
