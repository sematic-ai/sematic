export type ExtractContextType<T> = Exclude<
    T extends React.Context<infer U> ? U : never, 
    null>
