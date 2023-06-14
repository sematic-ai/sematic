import { Filter, FilterCondition } from "src/ApiContracts";

export enum FilterType {
    SEARCH = "search",
    TAGS = "tags",
    OWNER = "owner",
    STATUS = "status",
    OTHER = "other"
}

export type AllFilters = Partial<Record<FilterType, string[]>>;

export type StatusFilters = "completed" | "failed" | "running" | "canceled";

export function convertTagsFilterToRunFilters(filters: string[]): Filter | null {

    if (!!filters && filters.length > 0) {
        const conditions = filters.map((tag) => ({
            "tags": { contains: tag}
        }));        
        if (conditions.length > 1) {
            return {
                "OR": conditions
            }
        } 
        return conditions[0];
    }
    
    return null;
}

export function convertStatusFilterToRunFilters(filters: StatusFilters[]): Filter | null {
    const filtersSet = new Set(filters);

    const conditions: FilterCondition[] = [];

    if (filtersSet.has("completed")) {
        ["RESOLVED", "SUCCEEDED"].forEach((state) => {
            conditions.push({
                "future_state": {eq: state}
            });
        });
    }
    if (filtersSet.has("failed")) {
        ["FAILED", "NESTED_FAILED"].forEach((state) => {
            conditions.push({
                "future_state": {eq: state}
            });
        });
    }
    if (filtersSet.has("running")) {
        ["SCHEDULED", "RAN"].forEach((state) => {
            conditions.push({
                "future_state": {eq: state}
            });
        });
    }
    if (filtersSet.has("canceled")) {
        conditions.push({
            "future_state": {eq: "CANCELED"}
        });
    }

    if (conditions.length > 1) {
        return {
            "OR": conditions
        }
    }

    if (conditions.length === 0) {
        return null;
    }

    return conditions[0];
}

export function convertMiscellaneousFilterToRunFilters(filters: string[]): Filter | null {
    const filtersSet = new Set(filters);

    if (filtersSet.has("rootRunsOnly")) {
        return { parent_id: { eq: null } }
    }
    return null;
}


export function convertOwnersFilterToRunFilters(filters: string[]): Filter | null {

    if (!!filters && filters.length > 0) {
        const conditions = filters.map((owner) => ({
            "user_id": {eq: owner}
        }));
        if (conditions.length > 1) {
            return {
                "OR": conditions
            }
        } 
        return conditions[0];        
    }
    
    return null;
}
