# Code Map - Execution Flow (Call Graph)

```mermaid
%%{init: {'flowchart': {'curve': 'linear', 'defaultRenderer': 'elk', 'nodeSpacing': 100, 'rankSpacing': 100}, 'theme': 'dark'}}%%
graph TD
    subgraph FSG0["FILE: execution_graph_generator"]
        N53["trace_execution()"]
        N54["example_main()"]
    end
    subgraph FSG1["FILE: test_trace_map"]
        N0["run_map_command()"]
    end
    subgraph SG0["DIR: clickup_framework"]
        subgraph SG1["DIR: commands"]
            subgraph FSG2["FILE: assigned_command"]
                N8["calculate_depth()"]
            end
            subgraph FSG3["FILE: command_sync"]
                N11["get_task_name()"]
                N9["find_existing_task()"]
                N10["command_sync_command()"]
                N12["create_or_update_task()"]
                N13["discover_cli_commands()"]
            end
            subgraph FSG4["FILE: comment_commands"]
                N15["format_comment_node()"]
                N27["comment_delete_command()"]
            end
            subgraph FSG5["FILE: doc_commands"]
                N72["doc_create_command()"]
            end
            subgraph FSG6["FILE: folder_commands"]
                N48["folder_delete_command()"]
                N51["folder_create_command()"]
                N49["folder_update_command()"]
                N50["folder_get_command()"]
            end
            subgraph FSG7["FILE: git_reauthor_command"]
                N34["reauthor_command()"]
                N47["check_uncommitted_changes()"]
                N35["get_git_config()"]
            end
            subgraph FSG8["FILE: map_command"]
                N1["map_command()"]
            end
            subgraph FSG9["FILE: update_command"]
                N7["register_command()"]
            end
        end

        subgraph SG2["DIR: components"]
            subgraph FSG10["FILE: detail_view"]
                subgraph CSG11_0["CLASS: TaskDetailFormatter._format_comments"]
                    N16["format_comment_node()"]
                end
                subgraph CSG11_1["CLASS: TaskDetailFormatter._format_documents"]
                    N17["format_page_node()"]
                    N24["get_page_children()"]
                end
            end
            subgraph FSG11["FILE: task_formatter"]
                N25["get_comment_children()"]
                N28["format_comment_node()"]
            end
        end

        subgraph SG3["DIR: git"]
            subgraph FSG12["FILE: git_operations"]
                N38["push_to_remote()"]
                N41["create_commit()"]
                N36["get_current_branch()"]
                N39["get_commit_author()"]
                N37["get_uncommitted_changes()"]
                N40["stage_all_changes()"]
            end
            subgraph FSG13["FILE: url_generator"]
                N68["generate_branch_url()"]
                N69["generate_commit_url()"]
                N70["parse_remote_url()"]
                N71["generate_pr_url()"]
            end
        end

        subgraph SG4["DIR: utils"]
            subgraph FSG14["FILE: colors"]
                N18["status_color()"]
                N23["extract_category_from_name()"]
                N26["colorize()"]
                N21["strip_ansi()"]
                N22["get_task_emoji()"]
                N19["status_to_code()"]
                N20["_enable_vt100_mode()"]
            end
            subgraph FSG15["FILE: datetime"]
                N77["format_timestamp()"]
                N78["parse_timestamp()"]
                N79["format_duration()"]
            end
            subgraph FSG16["FILE: text"]
                N75["clean_html()"]
                N73["unescape_content()"]
                N76["format_list()"]
                N74["pluralize()"]
            end
        end

    end

    subgraph SG5["DIR: scripts"]
        subgraph FSG17["FILE: create_hierarchy_test_tasks"]
            N14["create_task()"]
        end
        subgraph FSG18["FILE: import_cli_docs"]
            N42["print_error()"]
            N45["print_success()"]
            N46["print_info()"]
            N44["show_usage()"]
            N43["print_warning()"]
        end
        subgraph FSG19["FILE: post_actions_to_clickup"]
            N30["determine_status_emoji()"]
            N32["get_run_url()"]
            N33["upload_screenshot_attachments()"]
            N31["get_commit_url()"]
        end
        subgraph FSG20["FILE: post_test_results_to_clickup"]
            N29["contains_markdown()"]
        end
    end

    %% Connections
    N30 --> N31
    N30 --> N32
    N30 --> N33
    N30 --> N14
    N30 --> N29
    N9 --> N10
    N9 --> N11
    N9 --> N12
    N9 --> N14
    N9 --> N13
    N15 --> N16
    N15 --> N25
    N15 --> N26
    N15 --> N27
    N15 --> N29
    N34 --> N35
    N34 --> N36
    N34 --> N42
    N34 --> N7
    N34 --> N47
    N41 --> N36
    N41 --> N37
    N41 --> N38
    N41 --> N39
    N41 --> N40
    N48 --> N49
    N48 --> N50
    N48 --> N7
    N48 --> N51
    N51 --> N49
    N51 --> N50
    N51 --> N48
    N51 --> N7
    N26 --> N19
    N26 --> N18
    N26 --> N20
    N26 --> N21
    N26 --> N22
    N58 --> N57
    N58 --> N55
    N58 --> N59
    N58 --> N60
    N58 --> N61
    N12 --> N10
    N12 --> N11
    N12 --> N13
    N12 --> N14
    N12 --> N9
    N45 --> N43
    N45 --> N42
    N45 --> N44
    N45 --> N46
    N78 --> N79
    N78 --> N77
    N35 --> N36
    N35 --> N42
    N35 --> N7
    N35 --> N34
    N35 --> N47
    N20 --> N19
    N20 --> N18
    N20 --> N21
    N20 --> N22
    N20 --> N23
    N68 --> N69
    N68 --> N70
    N68 --> N71
    N69 --> N70
    N69 --> N71
    N0 --> N1
    N0 --> N53
    N18 --> N19
    N18 --> N20
    N18 --> N21
    N18 --> N22
    N18 --> N23
    N67 --> N57
    N67 --> N58
    N67 --> N55
    N67 --> N59
    N67 --> N60
    N75 --> N74
    N75 --> N76
    N49 --> N50
    N49 --> N48
    N49 --> N7
    N49 --> N51
    N21 --> N19
    N21 --> N18
    N21 --> N20
    N21 --> N22
    N21 --> N23
    N66 --> N57
    N66 --> N58
    N66 --> N55
    N66 --> N59
    N66 --> N60
    N5 --> N6
    N59 --> N57
    N59 --> N58
    N59 --> N55
    N59 --> N60
    N59 --> N61
    N46 --> N43
    N46 --> N42
    N46 --> N45
    N46 --> N44
    N40 --> N36
    N40 --> N37
    N40 --> N38
    N40 --> N39
    N40 --> N41
    N44 --> N43
    N44 --> N42
    N44 --> N45
    N44 --> N46
    N31 --> N30
    N31 --> N32
    N31 --> N33
    N31 --> N14
    N31 --> N29
    N65 --> N57
    N65 --> N58
    N65 --> N55
    N65 --> N59
    N65 --> N60
    N62 --> N57
    N62 --> N58
    N62 --> N55
    N62 --> N59
    N62 --> N60
    N50 --> N49
    N50 --> N48
    N50 --> N7
    N50 --> N51
    N32 --> N30
    N32 --> N31
    N32 --> N33
    N32 --> N14
    N32 --> N29
    N17 --> N16
    N17 --> N18
    N17 --> N24
    N17 --> N15
    N17 --> N25
    N4 --> N5
    N47 --> N35
    N47 --> N36
    N47 --> N42
    N47 --> N7
    N47 --> N34
    N25 --> N16
    N25 --> N77
    N25 --> N18
    N25 --> N19
    N27 --> N16
    N27 --> N15
    N27 --> N25
    N27 --> N26
    N27 --> N28
    N42 --> N43
    N42 --> N44
    N42 --> N45
    N42 --> N46
    N39 --> N36
    N39 --> N37
    N39 --> N38
    N39 --> N40
    N39 --> N41
    N22 --> N19
    N22 --> N18
    N22 --> N20
    N22 --> N21
    N22 --> N23
    N73 --> N74
    N73 --> N75
    N73 --> N76
    N64 --> N57
    N64 --> N58
    N64 --> N55
    N64 --> N59
    N64 --> N60
    N10 --> N11
    N10 --> N12
    N10 --> N14
    N10 --> N13
    N10 --> N9
    N63 --> N57
    N63 --> N58
    N63 --> N55
    N63 --> N59
    N63 --> N60
    N13 --> N10
    N13 --> N11
    N13 --> N12
    N13 --> N14
    N13 --> N9
    N33 --> N30
    N33 --> N31
    N33 --> N32
    N33 --> N14
    N33 --> N29
    N77 --> N78
    N77 --> N79
    N19 --> N18
    N19 --> N20
    N19 --> N21
    N19 --> N22
    N19 --> N23
    N7 --> N8
    N7 --> N9
    N7 --> N15
    N7 --> N34
    N7 --> N48
    N72 --> N73
    N72 --> N26
    N53 --> N54
    N53 --> N55
    N53 --> N56
    N1 --> N2
    N1 --> N3
    N1 --> N4
    N1 --> N7
    N1 --> N52
    N76 --> N77
    N76 --> N75
    N76 --> N74
    N56 --> N57
    N56 --> N58
    N56 --> N59
    N56 --> N60
    N56 --> N61
    N54 --> N55
    N54 --> N53
    N54 --> N56
    N16 --> N17
    N16 --> N18
    N16 --> N24
    N16 --> N15
    N16 --> N25
    N11 --> N10
    N11 --> N12
    N11 --> N14
    N11 --> N13
    N11 --> N9
    N38 --> N36
    N38 --> N37
    N38 --> N39
    N38 --> N40
    N38 --> N41
    N24 --> N16
    N24 --> N17
    N24 --> N18
    N24 --> N15
    N24 --> N25
    N71 --> N69
    N71 --> N70
    N23 --> N19
    N23 --> N18
    N23 --> N20
    N23 --> N21
    N23 --> N22
    N36 --> N35
    N36 --> N37
    N36 --> N38
    N36 --> N42
    N36 --> N39
    N29 --> N30
    N29 --> N31
    N29 --> N32
    N29 --> N33
    N29 --> N14
    N37 --> N36
    N37 --> N38
    N37 --> N39
    N37 --> N40
    N37 --> N41
    N60 --> N57
    N60 --> N58
    N60 --> N55
    N60 --> N59
    N60 --> N61
    N79 --> N78
    N79 --> N77
    N70 --> N69
    N70 --> N71
    N43 --> N42
    N43 --> N44
    N43 --> N45
    N43 --> N46
    N74 --> N75
    N74 --> N76

    linkStyle 0 stroke:#06b6d4,stroke-width:3px
    linkStyle 1 stroke:#06b6d4,stroke-width:3px
    linkStyle 2 stroke:#06b6d4,stroke-width:3px
    linkStyle 3 stroke:#06b6d4,stroke-width:3px
    linkStyle 4 stroke:#06b6d4,stroke-width:3px
    linkStyle 5 stroke:#10b981,stroke-width:3px
    linkStyle 6 stroke:#10b981,stroke-width:3px
    linkStyle 7 stroke:#10b981,stroke-width:3px
    linkStyle 8 stroke:#06b6d4,stroke-width:3px
    linkStyle 9 stroke:#10b981,stroke-width:3px
    linkStyle 10 stroke:#f59e0b,stroke-width:3px
    linkStyle 11 stroke:#f59e0b,stroke-width:3px
    linkStyle 12 stroke:#10b981,stroke-width:3px
    linkStyle 13 stroke:#10b981,stroke-width:3px
    linkStyle 14 stroke:#06b6d4,stroke-width:3px
    linkStyle 15 stroke:#10b981,stroke-width:3px
    linkStyle 16 stroke:#ec4899,stroke-width:3px
    linkStyle 17 stroke:#06b6d4,stroke-width:3px
    linkStyle 18 stroke:#10b981,stroke-width:3px
    linkStyle 19 stroke:#10b981,stroke-width:3px
    linkStyle 20 stroke:#ec4899,stroke-width:3px
    linkStyle 21 stroke:#ec4899,stroke-width:3px
    linkStyle 22 stroke:#ec4899,stroke-width:3px
    linkStyle 23 stroke:#ec4899,stroke-width:3px
    linkStyle 24 stroke:#ec4899,stroke-width:3px
    linkStyle 25 stroke:#10b981,stroke-width:3px
    linkStyle 26 stroke:#10b981,stroke-width:3px
    linkStyle 27 stroke:#10b981,stroke-width:3px
    linkStyle 28 stroke:#10b981,stroke-width:3px
    linkStyle 29 stroke:#10b981,stroke-width:3px
    linkStyle 30 stroke:#10b981,stroke-width:3px
    linkStyle 31 stroke:#10b981,stroke-width:3px
    linkStyle 32 stroke:#10b981,stroke-width:3px
    linkStyle 33 stroke:#10b981,stroke-width:3px
    linkStyle 34 stroke:#10b981,stroke-width:3px
    linkStyle 35 stroke:#10b981,stroke-width:3px
    linkStyle 36 stroke:#10b981,stroke-width:3px
    linkStyle 37 stroke:#10b981,stroke-width:3px
    linkStyle 38 stroke:#8b5cf6,stroke-width:3px
    linkStyle 39 stroke:#8b5cf6,stroke-width:3px
    linkStyle 40 stroke:#8b5cf6,stroke-width:3px
    linkStyle 41 stroke:#8b5cf6,stroke-width:3px
    linkStyle 42 stroke:#8b5cf6,stroke-width:3px
    linkStyle 43 stroke:#10b981,stroke-width:3px
    linkStyle 44 stroke:#10b981,stroke-width:3px
    linkStyle 45 stroke:#10b981,stroke-width:3px
    linkStyle 46 stroke:#06b6d4,stroke-width:3px
    linkStyle 47 stroke:#10b981,stroke-width:3px
    linkStyle 48 stroke:#06b6d4,stroke-width:3px
    linkStyle 49 stroke:#06b6d4,stroke-width:3px
    linkStyle 50 stroke:#06b6d4,stroke-width:3px
    linkStyle 51 stroke:#06b6d4,stroke-width:3px
    linkStyle 52 stroke:#10b981,stroke-width:3px
    linkStyle 53 stroke:#10b981,stroke-width:3px
    linkStyle 54 stroke:#ec4899,stroke-width:3px
    linkStyle 55 stroke:#06b6d4,stroke-width:3px
    linkStyle 56 stroke:#10b981,stroke-width:3px
    linkStyle 57 stroke:#10b981,stroke-width:3px
    linkStyle 58 stroke:#10b981,stroke-width:3px
    linkStyle 59 stroke:#10b981,stroke-width:3px
    linkStyle 60 stroke:#10b981,stroke-width:3px
    linkStyle 61 stroke:#10b981,stroke-width:3px
    linkStyle 62 stroke:#10b981,stroke-width:3px
    linkStyle 63 stroke:#10b981,stroke-width:3px
    linkStyle 64 stroke:#ec4899,stroke-width:3px
    linkStyle 65 stroke:#ec4899,stroke-width:3px
    linkStyle 66 stroke:#ec4899,stroke-width:3px
    linkStyle 67 stroke:#ec4899,stroke-width:3px
    linkStyle 68 stroke:#ec4899,stroke-width:3px
    linkStyle 69 stroke:#10b981,stroke-width:3px
    linkStyle 70 stroke:#8b5cf6,stroke-width:3px
    linkStyle 71 stroke:#10b981,stroke-width:3px
    linkStyle 72 stroke:#10b981,stroke-width:3px
    linkStyle 73 stroke:#10b981,stroke-width:3px
    linkStyle 74 stroke:#10b981,stroke-width:3px
    linkStyle 75 stroke:#10b981,stroke-width:3px
    linkStyle 76 stroke:#8b5cf6,stroke-width:3px
    linkStyle 77 stroke:#8b5cf6,stroke-width:3px
    linkStyle 78 stroke:#8b5cf6,stroke-width:3px
    linkStyle 79 stroke:#8b5cf6,stroke-width:3px
    linkStyle 80 stroke:#8b5cf6,stroke-width:3px
    linkStyle 81 stroke:#10b981,stroke-width:3px
    linkStyle 82 stroke:#10b981,stroke-width:3px
    linkStyle 83 stroke:#10b981,stroke-width:3px
    linkStyle 84 stroke:#10b981,stroke-width:3px
    linkStyle 85 stroke:#10b981,stroke-width:3px
    linkStyle 86 stroke:#10b981,stroke-width:3px
    linkStyle 87 stroke:#10b981,stroke-width:3px
    linkStyle 88 stroke:#10b981,stroke-width:3px
    linkStyle 89 stroke:#10b981,stroke-width:3px
    linkStyle 90 stroke:#10b981,stroke-width:3px
    linkStyle 91 stroke:#10b981,stroke-width:3px
    linkStyle 92 stroke:#8b5cf6,stroke-width:3px
    linkStyle 93 stroke:#8b5cf6,stroke-width:3px
    linkStyle 94 stroke:#8b5cf6,stroke-width:3px
    linkStyle 95 stroke:#8b5cf6,stroke-width:3px
    linkStyle 96 stroke:#8b5cf6,stroke-width:3px
    linkStyle 97 stroke:#06b6d4,stroke-width:3px
    linkStyle 98 stroke:#8b5cf6,stroke-width:3px
    linkStyle 99 stroke:#8b5cf6,stroke-width:3px
    linkStyle 100 stroke:#8b5cf6,stroke-width:3px
    linkStyle 101 stroke:#8b5cf6,stroke-width:3px
    linkStyle 102 stroke:#8b5cf6,stroke-width:3px
    linkStyle 103 stroke:#06b6d4,stroke-width:3px
    linkStyle 104 stroke:#06b6d4,stroke-width:3px
    linkStyle 105 stroke:#06b6d4,stroke-width:3px
    linkStyle 106 stroke:#06b6d4,stroke-width:3px
    linkStyle 107 stroke:#ec4899,stroke-width:3px
    linkStyle 108 stroke:#ec4899,stroke-width:3px
    linkStyle 109 stroke:#ec4899,stroke-width:3px
    linkStyle 110 stroke:#ec4899,stroke-width:3px
    linkStyle 111 stroke:#ec4899,stroke-width:3px
    linkStyle 112 stroke:#06b6d4,stroke-width:3px
    linkStyle 113 stroke:#06b6d4,stroke-width:3px
    linkStyle 114 stroke:#06b6d4,stroke-width:3px
    linkStyle 115 stroke:#06b6d4,stroke-width:3px
    linkStyle 116 stroke:#06b6d4,stroke-width:3px
    linkStyle 117 stroke:#06b6d4,stroke-width:3px
    linkStyle 118 stroke:#06b6d4,stroke-width:3px
    linkStyle 119 stroke:#06b6d4,stroke-width:3px
    linkStyle 120 stroke:#06b6d4,stroke-width:3px
    linkStyle 121 stroke:#8b5cf6,stroke-width:3px
    linkStyle 122 stroke:#8b5cf6,stroke-width:3px
    linkStyle 123 stroke:#8b5cf6,stroke-width:3px
    linkStyle 124 stroke:#8b5cf6,stroke-width:3px
    linkStyle 125 stroke:#8b5cf6,stroke-width:3px
    linkStyle 126 stroke:#8b5cf6,stroke-width:3px
    linkStyle 127 stroke:#8b5cf6,stroke-width:3px
    linkStyle 128 stroke:#8b5cf6,stroke-width:3px
    linkStyle 129 stroke:#8b5cf6,stroke-width:3px
    linkStyle 130 stroke:#8b5cf6,stroke-width:3px
    linkStyle 131 stroke:#10b981,stroke-width:3px
    linkStyle 132 stroke:#10b981,stroke-width:3px
    linkStyle 133 stroke:#10b981,stroke-width:3px
    linkStyle 134 stroke:#10b981,stroke-width:3px
    linkStyle 135 stroke:#06b6d4,stroke-width:3px
    linkStyle 136 stroke:#06b6d4,stroke-width:3px
    linkStyle 137 stroke:#06b6d4,stroke-width:3px
    linkStyle 138 stroke:#06b6d4,stroke-width:3px
    linkStyle 139 stroke:#06b6d4,stroke-width:3px
    linkStyle 140 stroke:#f59e0b,stroke-width:3px
    linkStyle 141 stroke:#10b981,stroke-width:3px
    linkStyle 142 stroke:#f59e0b,stroke-width:3px
    linkStyle 143 stroke:#10b981,stroke-width:3px
    linkStyle 144 stroke:#f59e0b,stroke-width:3px
    linkStyle 145 stroke:#06b6d4,stroke-width:3px
    linkStyle 146 stroke:#10b981,stroke-width:3px
    linkStyle 147 stroke:#ec4899,stroke-width:3px
    linkStyle 148 stroke:#06b6d4,stroke-width:3px
    linkStyle 149 stroke:#10b981,stroke-width:3px
    linkStyle 150 stroke:#10b981,stroke-width:3px
    linkStyle 151 stroke:#f59e0b,stroke-width:3px
    linkStyle 152 stroke:#10b981,stroke-width:3px
    linkStyle 153 stroke:#10b981,stroke-width:3px
    linkStyle 154 stroke:#10b981,stroke-width:3px
    linkStyle 155 stroke:#f59e0b,stroke-width:3px
    linkStyle 156 stroke:#10b981,stroke-width:3px
    linkStyle 157 stroke:#f59e0b,stroke-width:3px
    linkStyle 158 stroke:#10b981,stroke-width:3px
    linkStyle 159 stroke:#f59e0b,stroke-width:3px
    linkStyle 160 stroke:#06b6d4,stroke-width:3px
    linkStyle 161 stroke:#06b6d4,stroke-width:3px
    linkStyle 162 stroke:#06b6d4,stroke-width:3px
    linkStyle 163 stroke:#06b6d4,stroke-width:3px
    linkStyle 164 stroke:#ec4899,stroke-width:3px
    linkStyle 165 stroke:#ec4899,stroke-width:3px
    linkStyle 166 stroke:#ec4899,stroke-width:3px
    linkStyle 167 stroke:#ec4899,stroke-width:3px
    linkStyle 168 stroke:#ec4899,stroke-width:3px
    linkStyle 169 stroke:#10b981,stroke-width:3px
    linkStyle 170 stroke:#10b981,stroke-width:3px
    linkStyle 171 stroke:#10b981,stroke-width:3px
    linkStyle 172 stroke:#10b981,stroke-width:3px
    linkStyle 173 stroke:#10b981,stroke-width:3px
    linkStyle 174 stroke:#10b981,stroke-width:3px
    linkStyle 175 stroke:#10b981,stroke-width:3px
    linkStyle 176 stroke:#10b981,stroke-width:3px
    linkStyle 177 stroke:#8b5cf6,stroke-width:3px
    linkStyle 178 stroke:#8b5cf6,stroke-width:3px
    linkStyle 179 stroke:#8b5cf6,stroke-width:3px
    linkStyle 180 stroke:#8b5cf6,stroke-width:3px
    linkStyle 181 stroke:#8b5cf6,stroke-width:3px
    linkStyle 182 stroke:#10b981,stroke-width:3px
    linkStyle 183 stroke:#10b981,stroke-width:3px
    linkStyle 184 stroke:#06b6d4,stroke-width:3px
    linkStyle 185 stroke:#10b981,stroke-width:3px
    linkStyle 186 stroke:#10b981,stroke-width:3px
    linkStyle 187 stroke:#8b5cf6,stroke-width:3px
    linkStyle 188 stroke:#8b5cf6,stroke-width:3px
    linkStyle 189 stroke:#8b5cf6,stroke-width:3px
    linkStyle 190 stroke:#8b5cf6,stroke-width:3px
    linkStyle 191 stroke:#8b5cf6,stroke-width:3px
    linkStyle 192 stroke:#10b981,stroke-width:3px
    linkStyle 193 stroke:#10b981,stroke-width:3px
    linkStyle 194 stroke:#10b981,stroke-width:3px
    linkStyle 195 stroke:#06b6d4,stroke-width:3px
    linkStyle 196 stroke:#10b981,stroke-width:3px
    linkStyle 197 stroke:#06b6d4,stroke-width:3px
    linkStyle 198 stroke:#06b6d4,stroke-width:3px
    linkStyle 199 stroke:#06b6d4,stroke-width:3px
    linkStyle 200 stroke:#06b6d4,stroke-width:3px
    linkStyle 201 stroke:#06b6d4,stroke-width:3px
    linkStyle 202 stroke:#10b981,stroke-width:3px
    linkStyle 203 stroke:#10b981,stroke-width:3px
    linkStyle 204 stroke:#10b981,stroke-width:3px
    linkStyle 205 stroke:#10b981,stroke-width:3px
    linkStyle 206 stroke:#10b981,stroke-width:3px
    linkStyle 207 stroke:#10b981,stroke-width:3px
    linkStyle 208 stroke:#10b981,stroke-width:3px
    linkStyle 209 stroke:#10b981,stroke-width:3px
    linkStyle 210 stroke:#10b981,stroke-width:3px
    linkStyle 211 stroke:#10b981,stroke-width:3px
    linkStyle 212 stroke:#10b981,stroke-width:3px
    linkStyle 213 stroke:#10b981,stroke-width:3px
    linkStyle 214 stroke:#10b981,stroke-width:3px
    linkStyle 215 stroke:#10b981,stroke-width:3px
    linkStyle 216 stroke:#8b5cf6,stroke-width:3px
    linkStyle 217 stroke:#8b5cf6,stroke-width:3px
    linkStyle 218 stroke:#8b5cf6,stroke-width:3px
    linkStyle 219 stroke:#8b5cf6,stroke-width:3px
    linkStyle 220 stroke:#8b5cf6,stroke-width:3px
    linkStyle 221 stroke:#06b6d4,stroke-width:3px
    linkStyle 222 stroke:#10b981,stroke-width:3px
    linkStyle 223 stroke:#8b5cf6,stroke-width:3px
    linkStyle 224 stroke:#10b981,stroke-width:3px
    linkStyle 225 stroke:#10b981,stroke-width:3px
    linkStyle 226 stroke:#10b981,stroke-width:3px
    linkStyle 227 stroke:#8b5cf6,stroke-width:3px
    linkStyle 228 stroke:#8b5cf6,stroke-width:3px
    linkStyle 229 stroke:#8b5cf6,stroke-width:3px
    linkStyle 230 stroke:#8b5cf6,stroke-width:3px
    linkStyle 231 stroke:#8b5cf6,stroke-width:3px
    linkStyle 232 stroke:#8b5cf6,stroke-width:3px
    linkStyle 233 stroke:#8b5cf6,stroke-width:3px
    linkStyle 234 stroke:#8b5cf6,stroke-width:3px
    linkStyle 235 stroke:#f59e0b,stroke-width:3px
    linkStyle 236 stroke:#10b981,stroke-width:3px
    linkStyle 237 stroke:#f59e0b,stroke-width:3px
    linkStyle 238 stroke:#10b981,stroke-width:3px
    linkStyle 239 stroke:#f59e0b,stroke-width:3px
    linkStyle 240 stroke:#10b981,stroke-width:3px
    linkStyle 241 stroke:#10b981,stroke-width:3px
    linkStyle 242 stroke:#06b6d4,stroke-width:3px
    linkStyle 243 stroke:#10b981,stroke-width:3px
    linkStyle 244 stroke:#10b981,stroke-width:3px
    linkStyle 245 stroke:#ec4899,stroke-width:3px
    linkStyle 246 stroke:#ec4899,stroke-width:3px
    linkStyle 247 stroke:#ec4899,stroke-width:3px
    linkStyle 248 stroke:#ec4899,stroke-width:3px
    linkStyle 249 stroke:#ec4899,stroke-width:3px
    linkStyle 250 stroke:#f59e0b,stroke-width:3px
    linkStyle 251 stroke:#f59e0b,stroke-width:3px
    linkStyle 252 stroke:#10b981,stroke-width:3px
    linkStyle 253 stroke:#10b981,stroke-width:3px
    linkStyle 254 stroke:#f59e0b,stroke-width:3px
    linkStyle 255 stroke:#ec4899,stroke-width:3px
    linkStyle 256 stroke:#ec4899,stroke-width:3px
    linkStyle 257 stroke:#10b981,stroke-width:3px
    linkStyle 258 stroke:#10b981,stroke-width:3px
    linkStyle 259 stroke:#10b981,stroke-width:3px
    linkStyle 260 stroke:#10b981,stroke-width:3px
    linkStyle 261 stroke:#10b981,stroke-width:3px
    linkStyle 262 stroke:#10b981,stroke-width:3px
    linkStyle 263 stroke:#ec4899,stroke-width:3px
    linkStyle 264 stroke:#ec4899,stroke-width:3px
    linkStyle 265 stroke:#06b6d4,stroke-width:3px
    linkStyle 266 stroke:#ec4899,stroke-width:3px
    linkStyle 267 stroke:#06b6d4,stroke-width:3px
    linkStyle 268 stroke:#06b6d4,stroke-width:3px
    linkStyle 269 stroke:#06b6d4,stroke-width:3px
    linkStyle 270 stroke:#06b6d4,stroke-width:3px
    linkStyle 271 stroke:#06b6d4,stroke-width:3px
    linkStyle 272 stroke:#ec4899,stroke-width:3px
    linkStyle 273 stroke:#ec4899,stroke-width:3px
    linkStyle 274 stroke:#ec4899,stroke-width:3px
    linkStyle 275 stroke:#ec4899,stroke-width:3px
    linkStyle 276 stroke:#ec4899,stroke-width:3px
    linkStyle 277 stroke:#8b5cf6,stroke-width:3px
    linkStyle 278 stroke:#8b5cf6,stroke-width:3px
    linkStyle 279 stroke:#8b5cf6,stroke-width:3px
    linkStyle 280 stroke:#8b5cf6,stroke-width:3px
    linkStyle 281 stroke:#8b5cf6,stroke-width:3px
    linkStyle 282 stroke:#10b981,stroke-width:3px
    linkStyle 283 stroke:#10b981,stroke-width:3px
    linkStyle 284 stroke:#ec4899,stroke-width:3px
    linkStyle 285 stroke:#ec4899,stroke-width:3px
    linkStyle 286 stroke:#06b6d4,stroke-width:3px
    linkStyle 287 stroke:#06b6d4,stroke-width:3px
    linkStyle 288 stroke:#06b6d4,stroke-width:3px
    linkStyle 289 stroke:#06b6d4,stroke-width:3px
    linkStyle 290 stroke:#10b981,stroke-width:3px
    linkStyle 291 stroke:#10b981,stroke-width:3px

    %% Styling - Green/Black/Purple Theme
    style SG0 fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px
    style SG1 fill:#1a1625,stroke:#8b5cf6,color:#8b5cf6,stroke-width:2px
    style SG2 fill:#0c1c20,stroke:#06b6d4,color:#06b6d4,stroke-width:2px
    style SG3 fill:#211a0d,stroke:#f59e0b,color:#f59e0b,stroke-width:2px
    style SG4 fill:#1f0d18,stroke:#ec4899,color:#ec4899,stroke-width:2px
    style SG5 fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px
    style FSG0 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG1 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG2 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG3 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG4 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG5 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG6 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG7 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG8 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG9 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG10 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG11 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG12 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG13 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG14 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG15 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG16 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG17 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG18 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG19 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style FSG20 fill:#1a1a1a,stroke:#10b981,color:#10b981,stroke-width:1px
    style CSG0_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG0_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG1_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG2_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG3_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG4_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG5_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG6_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG7_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG8_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG9_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG10_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG11_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG12_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG13_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG14_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG15_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG16_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG17_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG18_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG19_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_0 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_1 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_2 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_3 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_4 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_5 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_6 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_7 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_8 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style CSG20_9 fill:#0f0f0f,stroke:#8b5cf6,color:#8b5cf6,stroke-width:1px
    style N0 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N1 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N2 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N3 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N4 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
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
    style N18 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N19 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N20 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N21 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N22 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N23 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N24 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N25 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N26 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N27 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N28 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N29 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N30 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N31 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N32 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N33 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N34 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N35 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N36 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N37 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N38 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N39 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N40 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N41 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N42 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N43 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N44 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N45 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N46 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N47 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N48 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N49 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N50 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N51 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N52 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N53 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N54 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N55 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N56 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N57 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N58 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N59 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N60 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N61 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N62 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N63 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N64 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N65 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N66 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N67 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N68 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N69 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N70 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N71 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N72 fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7
    style N73 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N74 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N75 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N76 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N77 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N78 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
    style N79 fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981
```

## Legend
- **Purple nodes**: Entry points (functions not called by others)
- **Green-bordered nodes**: Called functions
- **DIR subgraphs**: Group by directory (scanned from filesystem)
- **FILE subgraphs**: Group related files (e.g., Component.razor + Component.razor.cs)
- **CLASS subgraphs**: Group by class when multiple classes in same file
- **Line numbers**: Show start-end lines in source file

## Statistics
- **Total Functions Mapped**: 80
- **Folders**: 8
- **File Components**: 25
- **Classes/Modules**: 30
- **Total Call Relationships**: 6864
- **Entry Points Found**: 10
- **Directory Tree Depth**: 3 (configurable)