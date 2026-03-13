# Code Map - Execution Flow (Call Graph)

```mermaid
%%{init: {'flowchart': {'curve': 'linear', 'defaultRenderer': 'elk', 'nodeSpacing': 100, 'rankSpacing': 100}, 'theme': 'dark'}}%%
graph TD
    subgraph SG0["DIR: clickup_framework"]
        subgraph FSG0["FILE: cli"]
            N54["_display_commands()"]
            N55["_format_task_create_examples()"]
            N63["_display_examples_and_footer()"]
            N64["_get_fallback_commands()"]
        end
        subgraph FSG1["FILE: mcp_server"]
            N57["resolve_resource_id()"]
            N58["handle_get_list_tasks()"]
            N59["handle_delete_comment()"]
            N60["handle_list_tools()"]
            N61["handle_set_custom_field()"]
            N62["handle_set_task_status()"]
        end
        subgraph SG1["DIR: formatters"]
            subgraph FSG2["FILE: list"]
                N43["format_list_collection()"]
            end
        end

        subgraph SG2["DIR: git"]
            subgraph FSG3["FILE: url_generator"]
                N0["generate_branch_url()"]
                N1["generate_pr_url()"]
                N2["generate_commit_url()"]
                N3["parse_remote_url()"]
            end
        end

        subgraph SG3["DIR: utils"]
            subgraph FSG4["FILE: animations"]
                N25["demo_animations()"]
            end
            subgraph FSG5["FILE: colors"]
                N27["priority_color()"]
                N28["get_status_icon()"]
                N29["get_progress_state()"]
                N30["get_task_emoji()"]
                N32["container_color()"]
                N31["completion_color()"]
                N26["colorize()"]
                N33["strip_ansi()"]
            end
            subgraph FSG6["FILE: datetime"]
                N36["format_timestamp()"]
                N38["parse_timestamp()"]
                N39["format_relative_time()"]
                N37["format_duration()"]
            end
            subgraph FSG7["FILE: text"]
                N40["truncate()"]
                N34["indent()"]
                N42["pluralize()"]
                N35["format_list()"]
                N41["clean_html()"]
            end
        end

    end

    subgraph SG4["DIR: scripts"]
        subgraph FSG8["FILE: post_actions_to_clickup"]
            N46["get_commit_url()"]
            N44["create_test_result_task()"]
            N52["get_task_type_breakdown()"]
            N53["get_workflow_run_info()"]
        end
        subgraph FSG9["FILE: post_test_results_to_clickup"]
            N45["contains_markdown()"]
            N48["create_actions_run_task()"]
            N47["upload_test_report_attachments()"]
            N49["load_test_report()"]
            N50["run_tests_with_coverage()"]
            N51["load_coverage_report()"]
        end
    end

    subgraph SG5["DIR: tests"]
        subgraph FSG10["FILE: test_hierarchy_display"]
            N56["main()"]
        end
        subgraph FSG11["FILE: test_profiling"]
            N4["my_function()"]
        end
        subgraph SG6["DIR: components"]
            subgraph FSG12["FILE: conftest"]
                N19["sample_tasks_with_comments()"]
                N24["sample_task_completed()"]
                N18["sample_docs_with_pages()"]
                N20["sample_task()"]
                N21["sample_container_tasks()"]
                N22["sample_page()"]
                N23["sample_doc()"]
            end
        end

    end

    %% Connections
    N47 --> N45
    N47 --> N46
    N47 --> N48
    N47 --> N49
    N47 --> N50
    N34 --> N35
    N34 --> N41
    N34 --> N40
    N34 --> N42
    N57 --> N58
    N57 --> N59
    N57 --> N60
    N57 --> N61
    N57 --> N62
    N4 --> N5
    N4 --> N10
    N4 --> N13
    N4 --> N12
    N4 --> N11
    N58 --> N57
    N58 --> N59
    N58 --> N60
    N58 --> N61
    N58 --> N62
    N32 --> N27
    N32 --> N28
    N32 --> N29
    N32 --> N30
    N32 --> N31
    N52 --> N45
    N52 --> N46
    N52 --> N47
    N52 --> N49
    N52 --> N51
    N59 --> N58
    N59 --> N57
    N59 --> N60
    N59 --> N61
    N59 --> N62
    N24 --> N19
    N24 --> N20
    N24 --> N21
    N24 --> N22
    N24 --> N23
    N60 --> N58
    N60 --> N57
    N60 --> N59
    N60 --> N61
    N60 --> N62
    N1 --> N2
    N1 --> N3
    N10 --> N6
    N10 --> N5
    N10 --> N7
    N10 --> N8
    N10 --> N9
    N25 --> N26
    N25 --> N33
    N41 --> N35
    N41 --> N40
    N41 --> N42
    N61 --> N58
    N61 --> N57
    N61 --> N59
    N61 --> N60
    N61 --> N62
    N62 --> N58
    N62 --> N57
    N62 --> N59
    N62 --> N60
    N62 --> N61
    N64 --> N55
    N64 --> N56
    N64 --> N26
    N26 --> N27
    N26 --> N28
    N26 --> N29
    N26 --> N30
    N26 --> N31
    N53 --> N45
    N53 --> N46
    N53 --> N47
    N53 --> N49
    N53 --> N52
    N43 --> N35
    N43 --> N36
    N19 --> N20
    N19 --> N21
    N19 --> N22
    N19 --> N23
    N19 --> N24
    N6 --> N5
    N6 --> N7
    N6 --> N8
    N6 --> N10
    N6 --> N12
    N27 --> N28
    N27 --> N29
    N27 --> N30
    N27 --> N31
    N27 --> N32
    N28 --> N27
    N28 --> N29
    N28 --> N30
    N28 --> N31
    N28 --> N32
    N44 --> N45
    N44 --> N46
    N44 --> N47
    N44 --> N49
    N44 --> N52
    N29 --> N27
    N29 --> N28
    N29 --> N30
    N29 --> N31
    N29 --> N32
    N16 --> N13
    N16 --> N14
    N16 --> N15
    N16 --> N17
    N42 --> N35
    N42 --> N41
    N42 --> N40
    N30 --> N27
    N30 --> N28
    N30 --> N29
    N30 --> N31
    N30 --> N32
    N45 --> N46
    N45 --> N48
    N45 --> N47
    N45 --> N49
    N45 --> N50
    N31 --> N27
    N31 --> N28
    N31 --> N29
    N31 --> N30
    N31 --> N32
    N2 --> N1
    N2 --> N3
    N48 --> N45
    N48 --> N47
    N48 --> N49
    N48 --> N50
    N48 --> N51
    N23 --> N19
    N23 --> N20
    N23 --> N21
    N23 --> N22
    N23 --> N24
    N14 --> N13
    N14 --> N15
    N14 --> N16
    N14 --> N17
    N37 --> N36
    N37 --> N38
    N37 --> N39
    N63 --> N55
    N63 --> N56
    N63 --> N26
    N55 --> N26
    N55 --> N56
    N56 --> N47
    N56 --> N57
    N56 --> N52
    N56 --> N60
    N56 --> N62
    N3 --> N1
    N3 --> N2
    N0 --> N1
    N0 --> N2
    N0 --> N3
    N5 --> N6
    N5 --> N7
    N5 --> N8
    N5 --> N9
    N5 --> N10
    N36 --> N37
    N36 --> N38
    N36 --> N39
    N38 --> N36
    N38 --> N37
    N38 --> N39
    N8 --> N6
    N8 --> N5
    N8 --> N9
    N8 --> N10
    N8 --> N11
    N46 --> N45
    N46 --> N47
    N46 --> N49
    N46 --> N52
    N46 --> N51
    N35 --> N36
    N35 --> N40
    N35 --> N42
    N35 --> N41
    N35 --> N43
    N21 --> N19
    N21 --> N20
    N21 --> N22
    N21 --> N23
    N21 --> N24
    N22 --> N19
    N22 --> N20
    N22 --> N21
    N22 --> N23
    N22 --> N24
    N51 --> N45
    N51 --> N46
    N51 --> N48
    N51 --> N47
    N51 --> N49
    N13 --> N14
    N13 --> N15
    N13 --> N16
    N13 --> N17
    N12 --> N6
    N12 --> N5
    N12 --> N7
    N12 --> N8
    N12 --> N9
    N17 --> N13
    N17 --> N14
    N17 --> N15
    N17 --> N16
    N33 --> N27
    N33 --> N28
    N33 --> N29
    N33 --> N30
    N33 --> N31
    N20 --> N19
    N20 --> N21
    N20 --> N22
    N20 --> N23
    N20 --> N24
    N39 --> N36
    N39 --> N37
    N39 --> N38
    N49 --> N45
    N49 --> N46
    N49 --> N48
    N49 --> N47
    N49 --> N50
    N50 --> N45
    N50 --> N48
    N50 --> N47
    N50 --> N49
    N50 --> N51
    N54 --> N55
    N54 --> N56
    N54 --> N26
    N11 --> N6
    N11 --> N5
    N11 --> N7
    N11 --> N8
    N11 --> N9
    N18 --> N19
    N18 --> N20
    N18 --> N21
    N18 --> N22
    N18 --> N23
    N15 --> N13
    N15 --> N14
    N15 --> N16
    N15 --> N17
    N40 --> N35
    N40 --> N41
    N40 --> N42

    linkStyle 0 stroke:#059669,stroke-width:3px
    linkStyle 1 stroke:#059669,stroke-width:3px
    linkStyle 2 stroke:#059669,stroke-width:3px
    linkStyle 3 stroke:#059669,stroke-width:3px
    linkStyle 4 stroke:#059669,stroke-width:3px
    linkStyle 5 stroke:#db2777,stroke-width:3px
    linkStyle 6 stroke:#db2777,stroke-width:3px
    linkStyle 7 stroke:#db2777,stroke-width:3px
    linkStyle 8 stroke:#db2777,stroke-width:3px
    linkStyle 9 stroke:#059669,stroke-width:3px
    linkStyle 10 stroke:#059669,stroke-width:3px
    linkStyle 11 stroke:#059669,stroke-width:3px
    linkStyle 12 stroke:#059669,stroke-width:3px
    linkStyle 13 stroke:#059669,stroke-width:3px
    linkStyle 14 stroke:#7c3aed,stroke-width:3px
    linkStyle 15 stroke:#7c3aed,stroke-width:3px
    linkStyle 16 stroke:#7c3aed,stroke-width:3px
    linkStyle 17 stroke:#7c3aed,stroke-width:3px
    linkStyle 18 stroke:#7c3aed,stroke-width:3px
    linkStyle 19 stroke:#059669,stroke-width:3px
    linkStyle 20 stroke:#059669,stroke-width:3px
    linkStyle 21 stroke:#059669,stroke-width:3px
    linkStyle 22 stroke:#059669,stroke-width:3px
    linkStyle 23 stroke:#059669,stroke-width:3px
    linkStyle 24 stroke:#db2777,stroke-width:3px
    linkStyle 25 stroke:#db2777,stroke-width:3px
    linkStyle 26 stroke:#db2777,stroke-width:3px
    linkStyle 27 stroke:#db2777,stroke-width:3px
    linkStyle 28 stroke:#db2777,stroke-width:3px
    linkStyle 29 stroke:#059669,stroke-width:3px
    linkStyle 30 stroke:#059669,stroke-width:3px
    linkStyle 31 stroke:#059669,stroke-width:3px
    linkStyle 32 stroke:#059669,stroke-width:3px
    linkStyle 33 stroke:#059669,stroke-width:3px
    linkStyle 34 stroke:#059669,stroke-width:3px
    linkStyle 35 stroke:#059669,stroke-width:3px
    linkStyle 36 stroke:#059669,stroke-width:3px
    linkStyle 37 stroke:#059669,stroke-width:3px
    linkStyle 38 stroke:#059669,stroke-width:3px
    linkStyle 39 stroke:#0891b2,stroke-width:3px
    linkStyle 40 stroke:#0891b2,stroke-width:3px
    linkStyle 41 stroke:#0891b2,stroke-width:3px
    linkStyle 42 stroke:#0891b2,stroke-width:3px
    linkStyle 43 stroke:#0891b2,stroke-width:3px
    linkStyle 44 stroke:#059669,stroke-width:3px
    linkStyle 45 stroke:#059669,stroke-width:3px
    linkStyle 46 stroke:#059669,stroke-width:3px
    linkStyle 47 stroke:#059669,stroke-width:3px
    linkStyle 48 stroke:#059669,stroke-width:3px
    linkStyle 49 stroke:#d97706,stroke-width:3px
    linkStyle 50 stroke:#d97706,stroke-width:3px
    linkStyle 51 stroke:#7c3aed,stroke-width:3px
    linkStyle 52 stroke:#7c3aed,stroke-width:3px
    linkStyle 53 stroke:#7c3aed,stroke-width:3px
    linkStyle 54 stroke:#7c3aed,stroke-width:3px
    linkStyle 55 stroke:#7c3aed,stroke-width:3px
    linkStyle 56 stroke:#db2777,stroke-width:3px
    linkStyle 57 stroke:#db2777,stroke-width:3px
    linkStyle 58 stroke:#db2777,stroke-width:3px
    linkStyle 59 stroke:#db2777,stroke-width:3px
    linkStyle 60 stroke:#db2777,stroke-width:3px
    linkStyle 61 stroke:#059669,stroke-width:3px
    linkStyle 62 stroke:#059669,stroke-width:3px
    linkStyle 63 stroke:#059669,stroke-width:3px
    linkStyle 64 stroke:#059669,stroke-width:3px
    linkStyle 65 stroke:#059669,stroke-width:3px
    linkStyle 66 stroke:#059669,stroke-width:3px
    linkStyle 67 stroke:#059669,stroke-width:3px
    linkStyle 68 stroke:#059669,stroke-width:3px
    linkStyle 69 stroke:#059669,stroke-width:3px
    linkStyle 70 stroke:#059669,stroke-width:3px
    linkStyle 71 stroke:#059669,stroke-width:3px
    linkStyle 72 stroke:#7c3aed,stroke-width:3px
    linkStyle 73 stroke:#db2777,stroke-width:3px
    linkStyle 74 stroke:#db2777,stroke-width:3px
    linkStyle 75 stroke:#db2777,stroke-width:3px
    linkStyle 76 stroke:#db2777,stroke-width:3px
    linkStyle 77 stroke:#db2777,stroke-width:3px
    linkStyle 78 stroke:#db2777,stroke-width:3px
    linkStyle 79 stroke:#059669,stroke-width:3px
    linkStyle 80 stroke:#059669,stroke-width:3px
    linkStyle 81 stroke:#059669,stroke-width:3px
    linkStyle 82 stroke:#059669,stroke-width:3px
    linkStyle 83 stroke:#059669,stroke-width:3px
    linkStyle 84 stroke:#db2777,stroke-width:3px
    linkStyle 85 stroke:#db2777,stroke-width:3px
    linkStyle 86 stroke:#0891b2,stroke-width:3px
    linkStyle 87 stroke:#0891b2,stroke-width:3px
    linkStyle 88 stroke:#0891b2,stroke-width:3px
    linkStyle 89 stroke:#0891b2,stroke-width:3px
    linkStyle 90 stroke:#0891b2,stroke-width:3px
    linkStyle 91 stroke:#7c3aed,stroke-width:3px
    linkStyle 92 stroke:#7c3aed,stroke-width:3px
    linkStyle 93 stroke:#7c3aed,stroke-width:3px
    linkStyle 94 stroke:#7c3aed,stroke-width:3px
    linkStyle 95 stroke:#7c3aed,stroke-width:3px
    linkStyle 96 stroke:#db2777,stroke-width:3px
    linkStyle 97 stroke:#db2777,stroke-width:3px
    linkStyle 98 stroke:#db2777,stroke-width:3px
    linkStyle 99 stroke:#db2777,stroke-width:3px
    linkStyle 100 stroke:#db2777,stroke-width:3px
    linkStyle 101 stroke:#db2777,stroke-width:3px
    linkStyle 102 stroke:#db2777,stroke-width:3px
    linkStyle 103 stroke:#db2777,stroke-width:3px
    linkStyle 104 stroke:#db2777,stroke-width:3px
    linkStyle 105 stroke:#db2777,stroke-width:3px
    linkStyle 106 stroke:#059669,stroke-width:3px
    linkStyle 107 stroke:#059669,stroke-width:3px
    linkStyle 108 stroke:#059669,stroke-width:3px
    linkStyle 109 stroke:#059669,stroke-width:3px
    linkStyle 110 stroke:#059669,stroke-width:3px
    linkStyle 111 stroke:#db2777,stroke-width:3px
    linkStyle 112 stroke:#db2777,stroke-width:3px
    linkStyle 113 stroke:#db2777,stroke-width:3px
    linkStyle 114 stroke:#db2777,stroke-width:3px
    linkStyle 115 stroke:#db2777,stroke-width:3px
    linkStyle 116 stroke:#7c3aed,stroke-width:3px
    linkStyle 117 stroke:#7c3aed,stroke-width:3px
    linkStyle 118 stroke:#7c3aed,stroke-width:3px
    linkStyle 119 stroke:#7c3aed,stroke-width:3px
    linkStyle 120 stroke:#db2777,stroke-width:3px
    linkStyle 121 stroke:#db2777,stroke-width:3px
    linkStyle 122 stroke:#db2777,stroke-width:3px
    linkStyle 123 stroke:#db2777,stroke-width:3px
    linkStyle 124 stroke:#db2777,stroke-width:3px
    linkStyle 125 stroke:#db2777,stroke-width:3px
    linkStyle 126 stroke:#db2777,stroke-width:3px
    linkStyle 127 stroke:#db2777,stroke-width:3px
    linkStyle 128 stroke:#059669,stroke-width:3px
    linkStyle 129 stroke:#059669,stroke-width:3px
    linkStyle 130 stroke:#059669,stroke-width:3px
    linkStyle 131 stroke:#059669,stroke-width:3px
    linkStyle 132 stroke:#059669,stroke-width:3px
    linkStyle 133 stroke:#db2777,stroke-width:3px
    linkStyle 134 stroke:#db2777,stroke-width:3px
    linkStyle 135 stroke:#db2777,stroke-width:3px
    linkStyle 136 stroke:#db2777,stroke-width:3px
    linkStyle 137 stroke:#db2777,stroke-width:3px
    linkStyle 138 stroke:#d97706,stroke-width:3px
    linkStyle 139 stroke:#d97706,stroke-width:3px
    linkStyle 140 stroke:#059669,stroke-width:3px
    linkStyle 141 stroke:#059669,stroke-width:3px
    linkStyle 142 stroke:#059669,stroke-width:3px
    linkStyle 143 stroke:#059669,stroke-width:3px
    linkStyle 144 stroke:#059669,stroke-width:3px
    linkStyle 145 stroke:#0891b2,stroke-width:3px
    linkStyle 146 stroke:#0891b2,stroke-width:3px
    linkStyle 147 stroke:#0891b2,stroke-width:3px
    linkStyle 148 stroke:#0891b2,stroke-width:3px
    linkStyle 149 stroke:#0891b2,stroke-width:3px
    linkStyle 150 stroke:#7c3aed,stroke-width:3px
    linkStyle 151 stroke:#7c3aed,stroke-width:3px
    linkStyle 152 stroke:#7c3aed,stroke-width:3px
    linkStyle 153 stroke:#7c3aed,stroke-width:3px
    linkStyle 154 stroke:#db2777,stroke-width:3px
    linkStyle 155 stroke:#db2777,stroke-width:3px
    linkStyle 156 stroke:#db2777,stroke-width:3px
    linkStyle 157 stroke:#059669,stroke-width:3px
    linkStyle 158 stroke:#7c3aed,stroke-width:3px
    linkStyle 159 stroke:#db2777,stroke-width:3px
    linkStyle 160 stroke:#db2777,stroke-width:3px
    linkStyle 161 stroke:#7c3aed,stroke-width:3px
    linkStyle 162 stroke:#059669,stroke-width:3px
    linkStyle 163 stroke:#059669,stroke-width:3px
    linkStyle 164 stroke:#059669,stroke-width:3px
    linkStyle 165 stroke:#059669,stroke-width:3px
    linkStyle 166 stroke:#059669,stroke-width:3px
    linkStyle 167 stroke:#d97706,stroke-width:3px
    linkStyle 168 stroke:#d97706,stroke-width:3px
    linkStyle 169 stroke:#d97706,stroke-width:3px
    linkStyle 170 stroke:#d97706,stroke-width:3px
    linkStyle 171 stroke:#d97706,stroke-width:3px
    linkStyle 172 stroke:#7c3aed,stroke-width:3px
    linkStyle 173 stroke:#7c3aed,stroke-width:3px
    linkStyle 174 stroke:#7c3aed,stroke-width:3px
    linkStyle 175 stroke:#7c3aed,stroke-width:3px
    linkStyle 176 stroke:#7c3aed,stroke-width:3px
    linkStyle 177 stroke:#db2777,stroke-width:3px
    linkStyle 178 stroke:#db2777,stroke-width:3px
    linkStyle 179 stroke:#db2777,stroke-width:3px
    linkStyle 180 stroke:#db2777,stroke-width:3px
    linkStyle 181 stroke:#db2777,stroke-width:3px
    linkStyle 182 stroke:#db2777,stroke-width:3px
    linkStyle 183 stroke:#7c3aed,stroke-width:3px
    linkStyle 184 stroke:#7c3aed,stroke-width:3px
    linkStyle 185 stroke:#7c3aed,stroke-width:3px
    linkStyle 186 stroke:#7c3aed,stroke-width:3px
    linkStyle 187 stroke:#7c3aed,stroke-width:3px
    linkStyle 188 stroke:#059669,stroke-width:3px
    linkStyle 189 stroke:#059669,stroke-width:3px
    linkStyle 190 stroke:#059669,stroke-width:3px
    linkStyle 191 stroke:#059669,stroke-width:3px
    linkStyle 192 stroke:#059669,stroke-width:3px
    linkStyle 193 stroke:#db2777,stroke-width:3px
    linkStyle 194 stroke:#db2777,stroke-width:3px
    linkStyle 195 stroke:#db2777,stroke-width:3px
    linkStyle 196 stroke:#db2777,stroke-width:3px
    linkStyle 197 stroke:#0891b2,stroke-width:3px
    linkStyle 198 stroke:#0891b2,stroke-width:3px
    linkStyle 199 stroke:#0891b2,stroke-width:3px
    linkStyle 200 stroke:#0891b2,stroke-width:3px
    linkStyle 201 stroke:#0891b2,stroke-width:3px
    linkStyle 202 stroke:#0891b2,stroke-width:3px
    linkStyle 203 stroke:#0891b2,stroke-width:3px
    linkStyle 204 stroke:#0891b2,stroke-width:3px
    linkStyle 205 stroke:#0891b2,stroke-width:3px
    linkStyle 206 stroke:#0891b2,stroke-width:3px
    linkStyle 207 stroke:#0891b2,stroke-width:3px
    linkStyle 208 stroke:#059669,stroke-width:3px
    linkStyle 209 stroke:#059669,stroke-width:3px
    linkStyle 210 stroke:#059669,stroke-width:3px
    linkStyle 211 stroke:#059669,stroke-width:3px
    linkStyle 212 stroke:#059669,stroke-width:3px
    linkStyle 213 stroke:#7c3aed,stroke-width:3px
    linkStyle 214 stroke:#7c3aed,stroke-width:3px
    linkStyle 215 stroke:#7c3aed,stroke-width:3px
    linkStyle 216 stroke:#7c3aed,stroke-width:3px
    linkStyle 217 stroke:#7c3aed,stroke-width:3px
    linkStyle 218 stroke:#7c3aed,stroke-width:3px
    linkStyle 219 stroke:#7c3aed,stroke-width:3px
    linkStyle 220 stroke:#7c3aed,stroke-width:3px
    linkStyle 221 stroke:#7c3aed,stroke-width:3px
    linkStyle 222 stroke:#7c3aed,stroke-width:3px
    linkStyle 223 stroke:#7c3aed,stroke-width:3px
    linkStyle 224 stroke:#7c3aed,stroke-width:3px
    linkStyle 225 stroke:#7c3aed,stroke-width:3px
    linkStyle 226 stroke:#db2777,stroke-width:3px
    linkStyle 227 stroke:#db2777,stroke-width:3px
    linkStyle 228 stroke:#db2777,stroke-width:3px
    linkStyle 229 stroke:#db2777,stroke-width:3px
    linkStyle 230 stroke:#db2777,stroke-width:3px
    linkStyle 231 stroke:#0891b2,stroke-width:3px
    linkStyle 232 stroke:#0891b2,stroke-width:3px
    linkStyle 233 stroke:#0891b2,stroke-width:3px
    linkStyle 234 stroke:#0891b2,stroke-width:3px
    linkStyle 235 stroke:#0891b2,stroke-width:3px
    linkStyle 236 stroke:#db2777,stroke-width:3px
    linkStyle 237 stroke:#db2777,stroke-width:3px
    linkStyle 238 stroke:#db2777,stroke-width:3px
    linkStyle 239 stroke:#059669,stroke-width:3px
    linkStyle 240 stroke:#059669,stroke-width:3px
    linkStyle 241 stroke:#059669,stroke-width:3px
    linkStyle 242 stroke:#059669,stroke-width:3px
    linkStyle 243 stroke:#059669,stroke-width:3px
    linkStyle 244 stroke:#059669,stroke-width:3px
    linkStyle 245 stroke:#059669,stroke-width:3px
    linkStyle 246 stroke:#059669,stroke-width:3px
    linkStyle 247 stroke:#059669,stroke-width:3px
    linkStyle 248 stroke:#059669,stroke-width:3px
    linkStyle 249 stroke:#059669,stroke-width:3px
    linkStyle 250 stroke:#7c3aed,stroke-width:3px
    linkStyle 251 stroke:#db2777,stroke-width:3px
    linkStyle 252 stroke:#7c3aed,stroke-width:3px
    linkStyle 253 stroke:#7c3aed,stroke-width:3px
    linkStyle 254 stroke:#7c3aed,stroke-width:3px
    linkStyle 255 stroke:#7c3aed,stroke-width:3px
    linkStyle 256 stroke:#7c3aed,stroke-width:3px
    linkStyle 257 stroke:#0891b2,stroke-width:3px
    linkStyle 258 stroke:#0891b2,stroke-width:3px
    linkStyle 259 stroke:#0891b2,stroke-width:3px
    linkStyle 260 stroke:#0891b2,stroke-width:3px
    linkStyle 261 stroke:#0891b2,stroke-width:3px
    linkStyle 262 stroke:#7c3aed,stroke-width:3px
    linkStyle 263 stroke:#7c3aed,stroke-width:3px
    linkStyle 264 stroke:#7c3aed,stroke-width:3px
    linkStyle 265 stroke:#7c3aed,stroke-width:3px
    linkStyle 266 stroke:#db2777,stroke-width:3px
    linkStyle 267 stroke:#db2777,stroke-width:3px
    linkStyle 268 stroke:#db2777,stroke-width:3px

    %% Styling - Light Theme
    style SG0 fill:#d1fae5,stroke:#059669,color:#047857,stroke-width:2px
    style SG1 fill:#ede9fe,stroke:#7c3aed,color:#6d28d9,stroke-width:2px
    style SG2 fill:#cffafe,stroke:#0891b2,color:#0e7490,stroke-width:2px
    style SG3 fill:#fef3c7,stroke:#d97706,color:#b45309,stroke-width:2px
    style SG4 fill:#fce7f3,stroke:#db2777,color:#be185d,stroke-width:2px
    style SG5 fill:#d1fae5,stroke:#059669,color:#047857,stroke-width:2px
    style SG6 fill:#ede9fe,stroke:#7c3aed,color:#6d28d9,stroke-width:2px
    style FSG0 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG1 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG2 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG3 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG4 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG5 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG6 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG7 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG8 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG9 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG10 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG11 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style FSG12 fill:#1a1a1a,stroke:#10b981,stroke-width:1px,color:#10b981
    style CSG0_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG0_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG1_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG2_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG3_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG4_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG5_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG6_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG7_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG8_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG9_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG10_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG11_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_0 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_1 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_2 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_3 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_4 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_5 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_6 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_7 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_8 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style CSG12_9 fill:#0f0f0f,stroke:#8b5cf6,stroke-width:1px,color:#8b5cf6
    style N0 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N1 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N2 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N3 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N4 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N5 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N6 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N7 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N8 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N9 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N10 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N11 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N12 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N13 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N14 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N15 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N16 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N17 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N18 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N19 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N20 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N21 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N22 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N23 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N24 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N25 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N26 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N27 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N28 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N29 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N30 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N31 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N32 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N33 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N34 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N35 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N36 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N37 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N38 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N39 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N40 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N41 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N42 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N43 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N44 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N45 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N46 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N47 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N48 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N49 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N50 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N51 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N52 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N53 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N54 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N55 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N56 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N57 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N58 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N59 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N60 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N61 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N62 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N63 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N64 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
```

## Legend
- **Purple nodes**: Entry points (functions not called by others)
- **Green-bordered nodes**: Called functions
- **DIR subgraphs**: Group by directory (scanned from filesystem)
- **FILE subgraphs**: Group related files (e.g., Component.razor + Component.razor.cs)
- **CLASS subgraphs**: Group by class when multiple classes in same file
- **Line numbers**: Show start-end lines in source file

## Statistics
- **Total Functions Mapped**: 65
- **Folders**: 8
- **File Components**: 15
- **Classes/Modules**: 17
- **Total Call Relationships**: 6932
- **Entry Points Found**: 10
- **Directory Tree Depth**: 3 (configurable)