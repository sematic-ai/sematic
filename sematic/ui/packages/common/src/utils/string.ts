export function getUserInitials(firstName: string | undefined | null,
    lastName: string | undefined | null, email: string | undefined | null) {
    return firstName ? `${firstName[0]}${lastName?.[0] || ""}` : email?.[0];
}
