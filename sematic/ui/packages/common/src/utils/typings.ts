export type ExtractContextType<T> = Exclude<
T extends React.Context<infer U> ? U : never, 
null>

export type RemoveUndefined<T> = {
    [P in keyof T]: Exclude<T[P], undefined>;
}
